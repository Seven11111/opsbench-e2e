import json, subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
def redis(command): return subprocess.run(['sh','-lc',command],capture_output=True,text=True,timeout=3)
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/catalog':
            value=redis('redis-cli -h redis GET catalog:v1').stdout.strip()
            try:
                data=json.loads(value)
                ok=data.get('version')==1 and isinstance(data.get('items'),list)
            except Exception:
                ok=False
        else:
            ok=self.path=='/health'
        self.send_response(200 if ok else 503); self.end_headers(); self.wfile.write(b'ok' if ok else b'cache payload invalid')
    def log_message(self,*a): pass
HTTPServer(('0.0.0.0',18087),H).serve_forever()
