import json
import urllib.request
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            body = b'opsbench_target_up 1\n'
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != '/opsbench/control':
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get('Content-Length', '0') or '0')
        try:
            payload = json.loads(self.rfile.read(length) or b'{}')
        except (json.JSONDecodeError, ValueError):
            payload = {}
        if payload.get('action') != 'restore':
            self.send_response(400)
            self.end_headers()
            return
        path = Path('/runtime/prometheus.yml')
        text = path.read_text(encoding='utf-8').replace('missing-exporter:19999', 'exporter:19100')
        path.write_text(text, encoding='utf-8')
        reload_ok = False
        try:
            request = urllib.request.Request('http://prometheus:9090/-/reload', method='POST')
            with urllib.request.urlopen(request, timeout=8) as response:
                reload_ok = int(response.status) == 200
        except OSError:
            pass
        body = json.dumps({'healthy': reload_ok, 'action': 'restore'}).encode('utf-8')
        self.send_response(200 if reload_ok else 503)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass

HTTPServer(('0.0.0.0', 19100), Handler).serve_forever()
