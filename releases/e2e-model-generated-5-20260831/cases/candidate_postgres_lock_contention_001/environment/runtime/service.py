import json, os, subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
def state(): return json.load(open('/runtime/state.json'))
def psql(sql):
    env=os.environ.copy(); env['PGPASSWORD']='opsbench-local-only'
    return subprocess.run(['psql','-h','db','-U','opsbench','-d','app','-At','-c',sql], env=env, capture_output=True, text=True, timeout=3)
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        ok=True; body='ok'
        if self.path == '/orders':
            q=psql("SET statement_timeout=700; SELECT pg_advisory_xact_lock(424242); SELECT count(*) FROM orders;")
            ok=q.returncode==0; body=q.stdout[-200:] if ok else 'database lock timeout'
        elif self.path != '/health': ok=False; body='not found'
        self.send_response(200 if ok else 503); self.end_headers(); self.wfile.write(body.encode())
    def log_message(self,*a): pass
HTTPServer(('0.0.0.0',18085),H).serve_forever()
