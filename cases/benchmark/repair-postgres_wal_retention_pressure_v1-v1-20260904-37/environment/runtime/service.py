import base64, json, os, socket, ssl, subprocess, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
ROOT=Path('/runtime'); CONTROL_ROOT=Path(os.environ.get('OPSBENCH_CONTROL_ROOT','/var/lib/opsbench/internal')); FAULT=CONTROL_ROOT/'fault.json'; STATUS=CONTROL_ROOT/'status.json'; TEMPLATE='fidelity_postgres_wal_retention_pressure_v1'
def fault():
    try: return json.loads(FAULT.read_text())
    except Exception: return {'mode':'baseline'}
def psql(sql):
    env=os.environ.copy(); env['PGPASSWORD']='opsbench-local-only'
    return subprocess.run(['psql','-h','db','-U','opsbench','-d','app','-At','-c',sql],env=env,capture_output=True,text=True,timeout=15)
def redis(args): return subprocess.run(['redis-cli','-h','redis',*args],capture_output=True,text=True,timeout=10)
def rabbit(path,method='GET',body=None):
    req=urllib.request.Request('http://rabbitmq:15672'+path,method=method,data=body)
    req.add_header('Authorization','Basic '+base64.b64encode(b'opsbench:opsbench-local-only').decode())
    req.add_header('Content-Type','application/json')
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req,timeout=8) as r: return r.status,r.read().decode()
    except Exception as exc: return 0,str(exc)
def rebuild_crl(revoked=False):
    d=ROOT/'tls'; index=d/'index.txt'
    rows=[]
    if index.exists():
        rows=[line for line in index.read_text().splitlines() if line.strip()]
    if rows:
        # OpenSSL's index.txt is a tab-separated certificate database.  The
        # revocation date field must be populated for an R record and must be
        # empty for a V record; changing only the status byte produces a
        # malformed database that makes ``openssl ca -gencrl`` abort and
        # disconnect the control client.
        now=time.strftime('%y%m%d%H%M%SZ',time.gmtime())
        normalized=[]
        for line in rows:
            fields=line.split('\t')
            if len(fields) >= 6:
                fields[0]='R' if revoked else 'V'
                fields[2]=now if revoked else ''
                normalized.append('\t'.join(fields))
            else:
                normalized.append(line)
        rows=normalized
        index.write_text('\n'.join(rows)+'\n')
    subprocess.run(['openssl','ca','-batch','-gencrl','-config',str(d/'openssl-ca.cnf'),'-out',str(d/'server.crl')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
def ensure_tls():
    d=ROOT/'tls'; d.mkdir(exist_ok=True)
    if (d/'server.crt').exists(): return
    subprocess.run("openssl req -x509 -newkey rsa:2048 -nodes -days 2 -subj /CN=OpsBenchRoot -addext basicConstraints=critical,CA:TRUE -addext keyUsage=critical,keyCertSign,cRLSign -keyout /runtime/tls/root.key -out /runtime/tls/root.crt >/dev/null 2>&1",shell=True,check=True)
    if TEMPLATE.startswith('fidelity_tls_revocation'):
        (d/'openssl-ca.cnf').write_text("""[ ca ]\ndefault_ca = CA_default\n[ CA_default ]\ndatabase = /runtime/tls/index.txt\nnew_certs_dir = /runtime/tls/newcerts\nserial = /runtime/tls/serial\ncrlnumber = /runtime/tls/crlnumber\ncertificate = /runtime/tls/root.crt\nprivate_key = /runtime/tls/root.key\ndefault_md = sha256\ndefault_days = 2\ndefault_crl_days = 2\npolicy = policy_any\ncopy_extensions = copy\n[ policy_any ]\ncommonName = supplied\n[ server_ext ]\nsubjectAltName = DNS:target,IP:127.0.0.1\nextendedKeyUsage = serverAuth\n""")
        (d/'newcerts').mkdir(exist_ok=True)
        (d/'serial').write_text('1000\n'); (d/'crlnumber').write_text('1000\n'); (d/'index.txt').write_text('')
        subprocess.run("openssl req -newkey rsa:2048 -nodes -subj /CN=target -keyout /runtime/tls/server.key -out /runtime/tls/server.csr >/dev/null 2>&1",shell=True,check=True)
        subprocess.run(['openssl','ca','-batch','-config',str(d/'openssl-ca.cnf'),'-extensions','server_ext','-in',str(d/'server.csr'),'-out',str(d/'server.crt')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        rebuild_crl(False)
        return
    if TEMPLATE.startswith('fidelity_tls_incomplete') or TEMPLATE.startswith('fidelity_tls_protocol'):
        subprocess.run("openssl req -newkey rsa:2048 -nodes -subj /CN=OpsBenchIntermediate -keyout /runtime/tls/intermediate.key -out /runtime/tls/intermediate.csr >/dev/null 2>&1",shell=True,check=True)
        subprocess.run("printf 'basicConstraints=critical,CA:TRUE,pathlen:0\\nkeyUsage=critical,keyCertSign,cRLSign' >/runtime/tls/intermediate.ext; openssl x509 -req -days 2 -in /runtime/tls/intermediate.csr -CA /runtime/tls/root.crt -CAkey /runtime/tls/root.key -CAcreateserial -extfile /runtime/tls/intermediate.ext -out /runtime/tls/intermediate.crt >/dev/null 2>&1",shell=True,check=True)
        subprocess.run("openssl req -newkey rsa:2048 -nodes -subj /CN=target -keyout /runtime/tls/server.key -out /runtime/tls/server.csr >/dev/null 2>&1; printf 'subjectAltName=DNS:target,IP:127.0.0.1\\nextendedKeyUsage=serverAuth' >/runtime/tls/server.ext; openssl x509 -req -days 2 -in /runtime/tls/server.csr -CA /runtime/tls/intermediate.crt -CAkey /runtime/tls/intermediate.key -CAcreateserial -extfile /runtime/tls/server.ext -out /runtime/tls/server.crt >/dev/null 2>&1",shell=True,check=True)
        (d/'server.fullchain.crt').write_text((d/'server.crt').read_text()+(d/'intermediate.crt').read_text())
    else:
        subprocess.run("openssl req -newkey rsa:2048 -nodes -subj /CN=target -keyout /runtime/tls/server.key -out /runtime/tls/server.csr >/dev/null 2>&1; printf 'subjectAltName=DNS:target,IP:127.0.0.1\\nextendedKeyUsage=serverAuth' >/runtime/tls/server.ext; openssl x509 -req -days 2 -in /runtime/tls/server.csr -CA /runtime/tls/root.crt -CAkey /runtime/tls/root.key -CAcreateserial -extfile /runtime/tls/server.ext -out /runtime/tls/server.crt >/dev/null 2>&1",shell=True,check=True)
    (d/'server.crl').write_text('healthy')
def backend_ok():
    if TEMPLATE.startswith('fidelity_postgres'): return psql('SELECT 1').returncode==0
    if TEMPLATE.startswith('fidelity_prometheus'):
        try:
            with urllib.request.urlopen('http://prometheus:9090/-/ready',timeout=5) as r: return r.status==200
        except Exception: return False
    if TEMPLATE.startswith('fidelity_rabbitmq'): return rabbit('/api/overview')[0]==200
    if TEMPLATE.startswith('fidelity_redis'): return redis(['PING']).returncode==0
    return True
def rabbit_consumer():
    if not TEMPLATE.startswith('fidelity_rabbitmq'): return
    try:
        import pika
    except Exception: return
    while True:
        try:
            conn=pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq',credentials=pika.PlainCredentials('opsbench','opsbench-local-only'),heartbeat=30,blocked_connection_timeout=5))
            ch=conn.channel(); ch.queue_declare(queue='opsbench-prefetch',durable=True); ch.basic_qos(prefetch_count=1)
            def on_message(channel, method, properties, body):
                if fault().get('mode')=='prefetch-starvation': time.sleep(30)
                channel.basic_ack(method.delivery_tag)
            ch.basic_consume(queue='opsbench-prefetch',on_message_callback=on_message,auto_ack=False)
            ch.start_consuming()
        except Exception:
            time.sleep(1)
def restore():
    if TEMPLATE.startswith('fidelity_postgres'): psql("SELECT pg_drop_replication_slot(slot_name) FROM pg_replication_slots WHERE slot_name LIKE 'opsbench_%'; CHECKPOINT;")
    elif TEMPLATE.startswith('fidelity_prometheus'):
        FAULT.write_text(json.dumps({'mode':'baseline'}))
        # A scrape can race the first delete_series call.  Repeat the bounded
        # cleanup after the target has switched back to its baseline metrics,
        # then reload Prometheus so the next scrape observes the repaired
        # state rather than a stale high-cardinality sample set.
        for _ in range(2):
            subprocess.run(['curl','--noproxy','*','-fsS','-X','POST','http://prometheus:9090/api/v1/admin/tsdb/delete_series?match%5B%5D=opsbench_request_total'],check=False)
            subprocess.run(['curl','--noproxy','*','-fsS','-X','POST','http://prometheus:9090/api/v1/admin/tsdb/clean_tombstones'],check=False)
            time.sleep(0.5)
        subprocess.run(['curl','--noproxy','*','-fsS','-X','POST','http://prometheus:9090/-/reload'],check=False)
        time.sleep(2)
    elif TEMPLATE.startswith('fidelity_rabbitmq'): rabbit('/api/queues/%2F/opsbench-prefetch/contents','DELETE')
    elif TEMPLATE.startswith('fidelity_redis'):
        (ROOT/'redis.conf').write_text('maxmemory-policy allkeys-lru\n'); redis(['CONFIG','SET','maxmemory-policy','allkeys-lru']); redis(['SET','opsbench:catalog','{"version":1,"items":["a","b"]}'])
    elif TEMPLATE.startswith('fidelity_tls_revocation'):
        FAULT.write_text(json.dumps({'mode':'baseline'})); rebuild_crl(False)
    else:
        FAULT.write_text(json.dumps({'mode':'baseline'}))
    FAULT.write_text(json.dumps({'mode':'baseline'})); return True
class Handler(BaseHTTPRequestHandler):
    def _reply(self, status, body):
        self.send_response(status); self.send_header('Content-Length', str(len(body))); self.send_header('Connection', 'close'); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=self.path.split('?',1)[0]; f=fault()
        if path=='/metrics' and TEMPLATE.startswith('fidelity_prometheus'):
            n=250 if f.get('mode')=='high-cardinality' else 3
            body=('opsbench_business_up 1\n'+'\n'.join(f'opsbench_request_total{{request_id="{i}"}} 1' for i in range(n))+'\n').encode()
            self._reply(200, body); return
        if path in {'/health','/business'}:
            ok=backend_ok()
            if TEMPLATE.startswith('fidelity_redis'): ok=ok and redis(['GET','opsbench:catalog']).stdout.strip().startswith('{"version"')
            STATUS.write_text(json.dumps({'healthy':ok,'mode':f.get('mode','baseline')}))
            self._reply(200 if ok else 503, b'ok' if ok else b'unhealthy'); return
        self._reply(404, b'not found')
    def do_POST(self):
        if self.path!='/opsbench/control': self.send_response(404); self.end_headers(); return
        n=int(self.headers.get('Content-Length','0') or '0'); payload=json.loads(self.rfile.read(n) or b'{}')
        if payload.get('action')=='restore': ok=restore()
        elif payload.get('action')=='set_revocation' and TEMPLATE.startswith('fidelity_tls_revocation'):
            FAULT.write_text(json.dumps({'mode':'revoked'})); rebuild_crl(True); ok=True
        else: ok=False
        self.send_response(200 if ok else 400); self.end_headers(); self.wfile.write(json.dumps({'healthy':ok}).encode())
    def log_message(self,*args): pass
class TLSServer(ThreadingHTTPServer):
    def get_request(self):
        sock,addr=super().get_request(); ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); mode=fault().get('mode')
        if TEMPLATE.startswith('fidelity_tls_protocol') and mode=='tls13-only': ctx.minimum_version=ssl.TLSVersion.TLSv1_3
        else: ctx.minimum_version=ssl.TLSVersion.TLSv1_2
        chain='/runtime/tls/server.crt' if TEMPLATE.startswith('fidelity_tls_incomplete') and mode=='incomplete-chain' else ('/runtime/tls/server.fullchain.crt' if (ROOT/'tls/server.fullchain.crt').exists() else '/runtime/tls/server.crt')
        ctx.load_cert_chain(chain,'/runtime/tls/server.key')
        try: return ctx.wrap_socket(sock,server_side=True),addr
        except Exception: sock.close(); raise
ensure_tls()
CONTROL_ROOT.mkdir(parents=True, exist_ok=True)
try: os.chmod(CONTROL_ROOT, 0o700)
except OSError: pass
if not FAULT.exists(): FAULT.write_text(json.dumps({'mode':'baseline'}))
if not STATUS.exists(): STATUS.write_text(json.dumps({'healthy':True,'mode':'baseline'}))
try: os.chmod(FAULT, 0o600); os.chmod(STATUS, 0o600)
except OSError: pass
http=ThreadingHTTPServer(('0.0.0.0',8080),Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
if TEMPLATE.startswith('fidelity_rabbitmq'):
    threading.Thread(target=rabbit_consumer,daemon=True).start()
if TEMPLATE.startswith('fidelity_tls'):
    tls=TLSServer(('0.0.0.0',8443),Handler)
    threading.Thread(target=tls.serve_forever,daemon=True).start()
while True:
    time.sleep(1)
