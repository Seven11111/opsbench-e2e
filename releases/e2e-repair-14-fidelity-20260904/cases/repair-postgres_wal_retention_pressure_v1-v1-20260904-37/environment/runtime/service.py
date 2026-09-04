import base64, json, os, socket, ssl, subprocess, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
ROOT=Path('/runtime'); FAULT=ROOT/'fault.json'; STATUS=ROOT/'status.json'; TEMPLATE='fidelity_postgres_wal_retention_pressure_v1'
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
        with urllib.request.urlopen(req,timeout=8) as r: return r.status,r.read().decode()
    except Exception as exc: return 0,str(exc)
def ensure_tls():
    d=ROOT/'tls'; d.mkdir(exist_ok=True)
    if (d/'server.crt').exists(): return
    subprocess.run("openssl req -x509 -newkey rsa:2048 -nodes -days 2 -subj /CN=OpsBenchRoot -keyout /runtime/tls/root.key -out /runtime/tls/root.crt >/dev/null 2>&1",shell=True,check=True)
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
    if TEMPLATE.startswith('fidelity_rabbitmq'): return rabbit('/api/health/checks/node')[0]==200
    if TEMPLATE.startswith('fidelity_redis'): return redis(['PING']).returncode==0
    return True
def restore():
    if TEMPLATE.startswith('fidelity_postgres'): psql("SELECT pg_drop_replication_slot(slot_name) FROM pg_replication_slots WHERE slot_name LIKE 'opsbench_%'; CHECKPOINT;")
    elif TEMPLATE.startswith('fidelity_prometheus'):
        FAULT.write_text(json.dumps({'mode':'baseline'})); subprocess.run(['curl','-fsS','-X','POST','http://prometheus:9090/-/reload'],check=False)
    elif TEMPLATE.startswith('fidelity_rabbitmq'): rabbit('/api/queues/%2F/opsbench-prefetch/contents','DELETE')
    elif TEMPLATE.startswith('fidelity_redis'): redis(['CONFIG','SET','maxmemory-policy','allkeys-lru']); redis(['SET','opsbench:catalog','{"version":1,"items":["a","b"]}'])
    else:
        FAULT.write_text(json.dumps({'mode':'baseline'}))
        if TEMPLATE.startswith('fidelity_tls_revocation'): (ROOT/'tls/server.crl').write_text('healthy')
    FAULT.write_text(json.dumps({'mode':'baseline'})); return True
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=self.path.split('?',1)[0]; f=fault()
        if path=='/metrics' and TEMPLATE.startswith('fidelity_prometheus'):
            n=250 if f.get('mode')=='high-cardinality' else 3
            body=('opsbench_business_up 1\n'+'\n'.join(f'opsbench_request_total{{request_id="{i}"}} 1' for i in range(n))+'\n').encode()
            self.send_response(200); self.end_headers(); self.wfile.write(body); return
        if path in {'/health','/business'}:
            ok=backend_ok()
            if TEMPLATE.startswith('fidelity_redis'): ok=ok and redis(['GET','opsbench:catalog']).stdout.strip().startswith('{"version"')
            STATUS.write_text(json.dumps({'healthy':ok,'mode':f.get('mode','baseline')}))
            self.send_response(200 if ok else 503); self.end_headers(); self.wfile.write(b'ok' if ok else b'unhealthy'); return
        self.send_response(404); self.end_headers()
    def do_POST(self):
        if self.path!='/opsbench/control': self.send_response(404); self.end_headers(); return
        n=int(self.headers.get('Content-Length','0') or '0'); payload=json.loads(self.rfile.read(n) or b'{}')
        ok=payload.get('action')=='restore' and restore(); self.send_response(200 if ok else 400); self.end_headers(); self.wfile.write(json.dumps({'healthy':ok}).encode())
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
http=ThreadingHTTPServer(('0.0.0.0',8080),Handler)
threading.Thread(target=http.serve_forever,daemon=True).start()
if TEMPLATE.startswith('fidelity_tls'):
    tls=TLSServer(('0.0.0.0',8443),Handler)
    threading.Thread(target=tls.serve_forever,daemon=True).start()
while True:
    time.sleep(1)
