import json, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
def read(): return json.load(open('/runtime/state.json'))
def effective_dependency(state): return state.get('override_dependency') or state.get('base_dependency') or 'downstream'
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        s=read(); ok=True
        if self.path == '/business':
            ok=False
            dependency=effective_dependency(s)
            # Keep the semantic fault as an invalid effective dependency,
            # but route it to the local downstream fixture so a failed
            # request returns promptly instead of blocking on DNS.
            host = 'downstream' if dependency in {'blackhole', 'downstream-blackhole'} else dependency
            url=f'http://{host}:18090/data'
            for _ in range(3):
                try:
                    with urllib.request.urlopen(url,timeout=.3) as r:
                        if r.status==200: ok=True; break
                except Exception: pass
            if not ok: s['circuit']='open'; open('/runtime/state.json','w').write(json.dumps(s))
            ok=ok and dependency=='downstream'
        elif self.path != '/health': ok=False
        self.send_response(200 if ok and s.get('circuit')!='open' else 503); self.end_headers(); self.wfile.write(b'ok' if ok else b'circuit open')
    def log_message(self,*a): pass
HTTPServer(('0.0.0.0',18089),H).serve_forever()
