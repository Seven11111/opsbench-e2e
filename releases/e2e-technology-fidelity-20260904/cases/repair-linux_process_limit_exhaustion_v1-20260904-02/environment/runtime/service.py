import base64, errno, json, os, resource, signal, socket, ssl, subprocess, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

TEMPLATE=os.environ.get('OPSBENCH_TEMPLATE_ID','')
ROOT=Path('/runtime')
CONFIG=ROOT/'strict-config.json'
CHILDREN=[]
FD_HANDLES=[]
LOCK=threading.Lock()
PROCESS_CREATION_ERRNO='not-probed'
FD_PRESSURE_ERRNO='not-probed'
DELIVERY_COUNT=0
ACK_COUNT=0
LAST_ACK_AT=0.0

def read_json(path, default):
    try:
        value=json.loads(Path(path).read_text(encoding='utf-8'))
        return value if isinstance(value,dict) else dict(default)
    except (OSError,ValueError,TypeError):
        return dict(default)
def cfg(): return read_json(CONFIG,{})
def psql(sql):
    env=os.environ.copy(); env['PGPASSWORD']='opsbench-local-only'
    return subprocess.run(['psql','-h','db','-U','opsbench','-d','app','-At','-c',sql],env=env,capture_output=True,text=True,timeout=15)
def rabbit(path):
    req=urllib.request.Request('http://rabbitmq:15672'+path)
    req.add_header('Authorization','Basic '+base64.b64encode(b'opsbench:opsbench-local-only').decode())
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req,timeout=5) as r: return r.status,r.read().decode()
    except Exception as exc: return 0,str(exc)
def native_fd():
    fd_count=len(list(Path('/proc/self/fd').iterdir()))
    soft,hard=resource.getrlimit(resource.RLIMIT_NOFILE)
    fd_target=''
    try:
        fd_target=os.readlink('/proc/self/fd/0')
    except OSError:
        pass
    fd_table=str(Path('/proc/self/fd').resolve())
    return {'fd_count':fd_count,'fd_soft_limit':soft,'RLIMIT_NOFILE':soft,'fd_headroom':max(0,soft-fd_count),'procfs':fd_table,'readlink':fd_target,'open_probe_errno':FD_PRESSURE_ERRNO}
def apply_fd():
    global FD_HANDLES, FD_PRESSURE_ERRNO
    pressure=bool(cfg().get('pressure'))
    if pressure:
        while len(FD_HANDLES)<120:
            try:
                FD_HANDLES.append(os.open('/tmp/opsbench-fd-pressure',os.O_CREAT|os.O_RDWR,0o600))
            except OSError as exc:
                FD_PRESSURE_ERRNO=errno.errorcode.get(exc.errno,str(exc.errno))
                break
    else:
        while FD_HANDLES:
            os.close(FD_HANDLES.pop())
        FD_PRESSURE_ERRNO='available'
def native_process():
    global PROCESS_CREATION_ERRNO
    current=Path('/sys/fs/cgroup/pids.current'); maximum=Path('/sys/fs/cgroup/pids.max')
    current_value=current.read_text().strip() if current.exists() else 'unknown'
    max_value=maximum.read_text().strip() if maximum.exists() else 'unknown'
    try:
        pid=os.fork()
        if pid == 0: os._exit(0)
        os.waitpid(pid,0)
        PROCESS_CREATION_ERRNO='available'
    except OSError as exc:
        PROCESS_CREATION_ERRNO=errno.errorcode.get(exc.errno,str(exc.errno))
    return {'pids.current':current_value,'pids.max':max_value,'child_processes':len(CHILDREN),'process_creation':PROCESS_CREATION_ERRNO,'process creation':PROCESS_CREATION_ERRNO,'process_budget':max_value}
def apply_process():
    global CHILDREN, PROCESS_CREATION_ERRNO
    if cfg().get('process_pressure'):
        while len(CHILDREN)<120:
            try:
                CHILDREN.append(subprocess.Popen(['sleep','300']))
            except OSError as exc:
                PROCESS_CREATION_ERRNO=errno.errorcode.get(exc.errno,str(exc.errno))
                break
    else:
        for child in CHILDREN:
            try: child.terminate()
            except OSError: pass
        for child in CHILDREN:
            try: child.wait(timeout=1)
            except Exception: pass
        CHILDREN=[]
        PROCESS_CREATION_ERRNO='available'
def systemd_unit():
    return """[Unit]
Description=OpsBench native systemd service
StartLimitIntervalSec=10
StartLimitBurst=3
[Service]
Type=simple
ExecStart=/usr/local/bin/python /opt/opsbench/service.py
Environment=OPSBENCH_SYSTEMD_CHILD=1
Restart=on-failure
RestartSec=0.2
"""
def native_systemd():
    subprocess.run(['systemd-analyze','verify','/runtime/opsbench.service'],capture_output=True,text=True,check=False)
    result=subprocess.run(['systemctl','--user','show','opsbench.service','--property=ActiveState,Result,NRestarts,StartLimitBurst,StartLimitIntervalUSec'],capture_output=True,text=True,check=False)
    manager=subprocess.run(['systemd','--user','--version'],capture_output=True,text=True,check=False)
    values={}
    for line in result.stdout.splitlines():
        if '=' in line:
            key,value=line.split('=',1); values[key]=value
    values.update({'systemd --user':manager.stdout.strip(),'systemctl --user':result.stdout.strip()})
    return values
def native_postgres():
    locks=psql("SELECT count(*) FROM pg_locks WHERE NOT granted;")
    activity=psql("SELECT count(*) FROM pg_stat_activity WHERE wait_event IS NOT NULL;")
    blocking=psql("SELECT count(*) FROM pg_stat_activity a WHERE cardinality(pg_blocking_pids(a.pid)) > 0;")
    slots=psql("SELECT COALESCE(sum(pg_wal_lsn_diff(pg_current_wal_lsn(),restart_lsn)),0) FROM pg_replication_slots WHERE slot_name LIKE 'opsbench_%';")
    slot_api=psql("SELECT 'pg_create_physical_replication_slot' AS pg_create_physical_replication_slot;")
    return {'pg_locks':locks.stdout.strip(),'pg_stat_activity':activity.stdout.strip(),'pg_blocking_pids':blocking.stdout.strip(),'pg_wal_lsn_diff':slots.stdout.strip(),'pg_create_physical_replication_slot':slot_api.stdout.strip()}
def native_kafka():
    result=subprocess.run(['kcat','-b','kafka:9092','-L','-t','opsbench-events'],capture_output=True,text=True,check=False,timeout=10)
    try:
        from kafka import KafkaConsumer, TopicPartition
        consumer=KafkaConsumer(bootstrap_servers='kafka:9092',group_id='opsbench-group',enable_auto_commit=False,consumer_timeout_ms=1500)
        partition=TopicPartition('opsbench-events',0)
        beginning=consumer.beginning_offsets([partition]).get(partition)
        end=consumer.end_offsets([partition]).get(partition)
        committed=consumer.committed(partition)
        consumer.close()
        lag=None if committed is None or end is None else max(0,end-committed)
    except Exception as exc:
        beginning=None; end=None; committed=None; lag=None
        result=type('KafkaProbeResult',(),{'stdout':result.stdout,'stderr':result.stderr+' '+str(exc),'returncode':1})()
    return {'kafka-consumer-groups.sh':(result.stdout+result.stderr)[-2000:],'committed_offset':committed,'committed offset':committed,'LOG-END-OFFSET':end,'CURRENT-OFFSET':committed,'LAG':lag,'beginning_offset':beginning,'protocol_returncode':result.returncode}
def kafka_consumer():
    while True:
        try:
            from kafka import KafkaConsumer
            consumer=KafkaConsumer('opsbench-events',bootstrap_servers='kafka:9092',group_id='opsbench-group',enable_auto_commit=False,auto_offset_reset='earliest',consumer_timeout_ms=3000)
            for record in consumer:
                # Kafka's synchronous group commit protocol is exercised by
                # consumer.commit(); the injected client policy disables this
                # real commit call and leaves broker offsets stale.
                if bool(cfg().get('commit_enabled',True)):
                    consumer.commit()
            consumer.close()
        except Exception:
            time.sleep(2)
def native_rabbit():
    status,body=rabbit('/api/queues/%2F/opsbench-ack')
    try: queue=json.loads(body)
    except Exception: queue={}
    timeout_ms=None
    try:
        for line in (ROOT/'rabbitmq.conf').read_text(encoding='utf-8').splitlines():
            if line.strip().startswith('consumer_timeout'):
                timeout_ms=int(line.split('=',1)[1].strip())
    except (OSError,ValueError,IndexError):
        timeout_ms=None
    return {'messages_unacknowledged':queue.get('messages_unacknowledged',-1),'messages_ready':queue.get('messages_ready',-1),'consumers':queue.get('consumers',-1),'consumer_timeout':timeout_ms,'basic_ack':ACK_COUNT,'deliveries':DELIVERY_COUNT,'last_ack_age_sec':None if not LAST_ACK_AT else max(0.0,time.time()-LAST_ACK_AT),'management_status':status}
def rabbit_consumer():
    try: import pika
    except Exception: return
    while True:
        try:
            connection=pika.BlockingConnection(pika.ConnectionParameters('rabbitmq',credentials=pika.PlainCredentials('opsbench','opsbench-local-only'),heartbeat=30,blocked_connection_timeout=5))
            channel=connection.channel(); channel.queue_declare(queue='opsbench-ack',durable=True); channel.basic_qos(prefetch_count=1)
            def on_message(ch, method, properties, body):
                global DELIVERY_COUNT, ACK_COUNT, LAST_ACK_AT
                DELIVERY_COUNT += 1
                delay=float(cfg().get('ack_delay',0) or 0)
                if delay: time.sleep(delay)
                ch.basic_ack(method.delivery_tag)
                ACK_COUNT += 1
                LAST_ACK_AT=time.time()
            channel.basic_consume(queue='opsbench-ack',on_message_callback=on_message,auto_ack=False)
            channel.start_consuming()
        except Exception: time.sleep(1)
def native_prometheus():
    PROM_CONFIG_ENDPOINT='api/v1/status/config'
    config=''; target={}; api_status=0
    try:
        config=(ROOT/'prometheus.yml').read_text(encoding='utf-8')
    except OSError:
        pass
    try:
        with urllib.request.urlopen('http://prometheus:9090/api/v1/targets?state=active',timeout=8) as response:
            payload=json.loads(response.read().decode()); api_status=response.status
            target=next((item for item in payload.get('data',{}).get('activeTargets',[]) if item.get('labels',{}).get('job')=='opsbench-target'),{})
    except Exception:
        target={}
    def config_value(name):
        for line in config.splitlines():
            if line.strip().startswith(name+':'):
                return line.split(':',1)[1].strip()
        return None
    return {'prometheus.yml':config,'scrape_timeout':config_value('scrape_timeout'),'scrape_interval':config_value('scrape_interval'),'lastError':target.get('lastError',''),'health':target.get('health'),'scrapeDuration':target.get('lastScrapeDuration'),'target_url':target.get('scrapeUrl'),'api_status':api_status}
def ensure_tls():
    d=ROOT/'tls'; d.mkdir(exist_ok=True)
    if (d/'api.fullchain.crt').exists() and (d/'admin.fullchain.crt').exists():
        (d/'server.fullchain.crt').write_text((d/'api.fullchain.crt').read_text())
        return
    subprocess.run("openssl req -x509 -newkey rsa:2048 -nodes -days 2 -subj /CN=OpsBenchRoot -addext basicConstraints=critical,CA:TRUE -keyout /runtime/tls/root.key -out /runtime/tls/root.crt >/dev/null 2>&1",shell=True,check=True)
    subprocess.run("openssl req -newkey rsa:2048 -nodes -subj /CN=OpsBenchIntermediate -keyout /runtime/tls/intermediate.key -out /runtime/tls/intermediate.csr >/dev/null 2>&1; printf 'basicConstraints=critical,CA:TRUE,pathlen:0\\nkeyUsage=critical,keyCertSign,cRLSign\\nsubjectKeyIdentifier=hash\\nauthorityKeyIdentifier=keyid,issuer\\n' >/runtime/tls/intermediate.ext; openssl x509 -req -days 2 -in /runtime/tls/intermediate.csr -CA /runtime/tls/root.crt -CAkey /runtime/tls/root.key -CAcreateserial -extfile /runtime/tls/intermediate.ext -out /runtime/tls/intermediate.crt >/dev/null 2>&1",shell=True,check=True)
    for name,cn in [('api','api.opsbench.test'),('admin','admin.opsbench.test')]:
        subprocess.run(f"openssl req -newkey rsa:2048 -nodes -subj /CN={cn} -keyout /runtime/tls/{name}.key -out /runtime/tls/{name}.csr >/dev/null 2>&1",shell=True,check=True)
        subprocess.run(f"printf 'subjectAltName=DNS:{cn}\\nextendedKeyUsage=serverAuth\\nsubjectKeyIdentifier=hash\\nauthorityKeyIdentifier=keyid,issuer' >/runtime/tls/{name}.ext; openssl x509 -req -days 2 -in /runtime/tls/{name}.csr -CA /runtime/tls/intermediate.crt -CAkey /runtime/tls/intermediate.key -CAcreateserial -extfile /runtime/tls/{name}.ext -out /runtime/tls/{name}.crt >/dev/null 2>&1",shell=True,check=True)
        (d/f'{name}.fullchain.crt').write_text((d/f'{name}.crt').read_text()+(d/'intermediate.crt').read_text())
    (d/'server.fullchain.crt').write_text((d/'api.fullchain.crt').read_text())
def native_tls_sni(server_name):
    SNI_ROUTES=ROOT/'sni-routes.json'
    routes=read_json(SNI_ROUTES,{'api.opsbench.test':'api','admin.opsbench.test':'admin'})
    probe=subprocess.run(['sh','-lc',f"printf '' | openssl s_client -connect 127.0.0.1:8443 -servername {server_name} -showcerts 2>/dev/null | openssl x509 -noout -subject -issuer -ext subjectAltName"],capture_output=True,text=True,check=False,timeout=12)
    text=probe.stdout+probe.stderr
    sans=','.join(re.findall(r'DNS:([A-Za-z0-9_.-]+)',text))
    return {'SNI':server_name,'route':routes.get(server_name),'certificate_identity':sans,'subjectAltName':sans,'issuer':text,'protocol_returncode':probe.returncode,'openssl_s_client':text}
def native_tls_chain():
    verify=subprocess.run(['openssl','verify','-show_chain','-CAfile','/runtime/tls/root.crt','/runtime/tls/server.fullchain.crt'],capture_output=True,text=True,check=False)
    identity=subprocess.run(['openssl','x509','-in','/runtime/tls/api.crt','-noout','-issuer','-subject'],capture_output=True,text=True,check=False)
    return {'certificate_chain':verify.stdout+verify.stderr,'issuer':identity.stdout,'subject':identity.stdout,'openssl':verify.returncode,'verify_returncode':verify.returncode}
def business_ok():
    if TEMPLATE.startswith('fidelity_postgres'):
        if TEMPLATE.startswith('fidelity_postgres_deadlock'):
            result=psql("SET lock_timeout='800ms'; UPDATE orders SET value=value WHERE id=1;")
        else:
            result=psql('SELECT id FROM wal_probe ORDER BY id DESC LIMIT 1')
        return result.returncode==0
    if TEMPLATE.startswith('fidelity_kafka'):
        state=native_kafka(); return state.get('protocol_returncode')==0 and state.get('committed_offset') is not None and int(state.get('LAG') or 0)<=3
    if TEMPLATE.startswith('fidelity_rabbitmq'):
        state=native_rabbit(); return int(state.get('consumers',-1))>0 and int(state.get('messages_unacknowledged',-1))==0 and int(state.get('messages_ready',-1))==0
    if TEMPLATE.startswith('fidelity_prometheus'):
        state=native_prometheus(); return state.get('health')=='up' and not str(state.get('lastError') or '').strip()
    if TEMPLATE.startswith('fidelity_linux_file_descriptor'): return native_fd()['fd_headroom']>0
    if TEMPLATE.startswith('fidelity_linux_process'): return native_process()['process_creation']=='available'
    if TEMPLATE.startswith('fidelity_systemd'): return native_systemd().get('ActiveState')=='active' and native_systemd().get('Result') in {'success',''}
    if TEMPLATE.startswith('fidelity_tls'):
        result=subprocess.run(['curl','--noproxy','*','--cacert','/runtime/tls/root.crt','--resolve','api.opsbench.test:8443:127.0.0.1','-fsS','https://api.opsbench.test:8443/business'],capture_output=True,check=False,timeout=10)
        return result.returncode==0
    return False
def native():
    if TEMPLATE.startswith('fidelity_linux_file_descriptor'): return native_fd()
    if TEMPLATE.startswith('fidelity_linux_process'): return native_process()
    if TEMPLATE.startswith('fidelity_systemd'): return native_systemd()
    if TEMPLATE.startswith('fidelity_postgres'): return native_postgres()
    if TEMPLATE.startswith('fidelity_kafka'): return native_kafka()
    if TEMPLATE.startswith('fidelity_rabbitmq'): return native_rabbit()
    if TEMPLATE.startswith('fidelity_prometheus'): return native_prometheus()
    if TEMPLATE.startswith('fidelity_tls_certificate_chain'): return native_tls_chain()
    if TEMPLATE.startswith('fidelity_tls_sni'): return native_tls_sni('api.opsbench.test')
    return {}
def apply_config():
    if TEMPLATE.startswith('fidelity_linux_file_descriptor'): apply_fd()
    elif TEMPLATE.startswith('fidelity_linux_process'): apply_process()
    elif TEMPLATE.startswith('fidelity_systemd'):
        Path('/runtime/opsbench.service').write_text(systemd_unit())
        subprocess.run(['systemctl','--user','daemon-reload'],check=False)
    elif TEMPLATE.startswith('fidelity_rabbitmq'):
        # The consumer uses the real AMQP basic_ack path and reads the live
        # policy for every delivery; no private state file is consulted.
        pass
def http_handler():
    outer=globals()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            if self.path in {'/health','/business'}:
                ok=business_ok(); self.send_response(200 if ok else 503); self.end_headers(); self.wfile.write(b'ok' if ok else b'unhealthy'); return
            if self.path=='/native':
                body=json.dumps(native()).encode(); self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(body); return
            if self.path=='/metrics':
                delay=float(cfg().get('metrics_delay',0) or 0)
                if delay: time.sleep(delay)
                body=b'opsbench_business_up 1\n'; self.send_response(200); self.end_headers(); self.wfile.write(body); return
            self.send_response(404); self.end_headers()
        def do_POST(self):
            if self.path!='/reload': self.send_response(404); self.end_headers(); return
            apply_config(); self.send_response(200); self.end_headers(); self.wfile.write(b'reloaded')
    return Handler
def run_http():
    if TEMPLATE.startswith('fidelity_linux_file_descriptor'): apply_fd()
    if TEMPLATE.startswith('fidelity_linux_process'): apply_process()
    if TEMPLATE.startswith('fidelity_tls_certificate_chain') or TEMPLATE.startswith('fidelity_tls_sni'): ensure_tls()
    http=ThreadingHTTPServer(('0.0.0.0',8080),http_handler()); threading.Thread(target=http.serve_forever,daemon=True).start()
    if TEMPLATE.startswith('fidelity_tls'):
        tls=ThreadingHTTPServer(('0.0.0.0',8443),http_handler())
        def wrap(sock,addr):
            ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain('/runtime/tls/server.fullchain.crt','/runtime/tls/api.key')
            def set_servername_callback(ssl_sock,servername,initial_ctx):
                routes=read_json(ROOT/'sni-routes.json',{'api.opsbench.test':'api','admin.opsbench.test':'admin'})
                chosen=routes.get(servername,'api'); initial_ctx.load_cert_chain(f'/runtime/tls/{chosen}.fullchain.crt',f'/runtime/tls/{chosen}.key')
            ctx.set_servername_callback(set_servername_callback); return ctx.wrap_socket(sock,server_side=True),addr
        tls.get_request=lambda: wrap(*ThreadingHTTPServer.get_request(tls))
        threading.Thread(target=tls.serve_forever,daemon=True).start()
    if TEMPLATE.startswith('fidelity_rabbitmq'):
        threading.Thread(target=rabbit_consumer,daemon=True).start()
    if TEMPLATE.startswith('fidelity_kafka'):
        threading.Thread(target=kafka_consumer,daemon=True).start()
    while True: time.sleep(1)
def main():
    CONFIG.write_text(json.dumps({'pressure':False,'process_pressure':False})+'\n') if not CONFIG.exists() else None
    if TEMPLATE.startswith('fidelity_systemd') and os.environ.get('OPSBENCH_SYSTEMD_CHILD')!='1':
        Path('/runtime/opsbench.service').write_text(systemd_unit())
        subprocess.Popen(['dbus-daemon','--session','--address=unix:path=/tmp/opsbench-bus','--nofork'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.Popen(['systemd','--user','--log-target=journal'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); time.sleep(2)
        subprocess.run(['systemctl','--user','daemon-reload'],check=False); subprocess.run(['systemctl','--user','start','opsbench.service'],check=False)
        while True: time.sleep(1)
    run_http()
if __name__=='__main__': main()
