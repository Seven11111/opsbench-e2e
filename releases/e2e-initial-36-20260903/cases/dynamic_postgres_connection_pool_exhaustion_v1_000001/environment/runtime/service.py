import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        ok=True; body='ok'
        if self.path == '/query':
            q=subprocess.run(['sh','-lc', "PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c 'SELECT count(*) FROM pool_probe'"],capture_output=True,text=True,timeout=4)
            ok=q.returncode==0; body=q.stdout[-100:] if ok else q.stderr[-200:]
        elif self.path != '/health': ok=False
        self.send_response(200 if ok else 503); self.end_headers(); self.wfile.write(body.encode())
    def log_message(self,*a): pass
HTTPServer(('0.0.0.0',18086),H).serve_forever()
