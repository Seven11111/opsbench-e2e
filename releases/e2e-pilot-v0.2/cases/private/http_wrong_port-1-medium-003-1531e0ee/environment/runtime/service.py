import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

runtime = Path(__file__).parent

def read_config():
    return json.loads((runtime / "config.json").read_text())

def update_status(healthy):
    (runtime / "status.json").write_text(json.dumps({"healthy": healthy}))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        config = read_config()
        healthy = int(config.get("port", 0)) == 18080
        update_status(healthy)
        self.send_response(200 if self.path == "/health" and healthy else 503)
        self.end_headers()
        self.wfile.write(b"ok" if healthy else b"unhealthy")
    def log_message(self, *_args):
        pass

update_status(read_config().get("port") == 18080)
HTTPServer(("0.0.0.0", 18080), Handler).serve_forever()
