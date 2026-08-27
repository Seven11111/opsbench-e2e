import json
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        s=json.load(open('/runtime/state.json')); dependency=s.get('override_dependency') or s.get('base_dependency') or 'downstream'; ok=s.get('mode')=='baseline' and dependency=='downstream'
        self.send_response(200 if ok else 503); self.end_headers(); self.wfile.write(b'data' if ok else b'downstream failure')
    def log_message(self,*a): pass
HTTPServer(('0.0.0.0',18090),H).serve_forever()
