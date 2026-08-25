import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

runtime = Path("/runtime")
forward_port = int(os.environ.get("OPSBENCH_FORWARD_PORT", "18080"))

def read_config():
    return json.loads((runtime / "config.json").read_text())

def update_status(healthy):
    (runtime / "status.json").write_text(json.dumps({"healthy": healthy}))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        config = read_config()
        healthy = int(config.get("port", 0)) == forward_port
        update_status(healthy)
        self.send_response(200 if self.path == "/health" and healthy else 503)
        self.end_headers()
        self.wfile.write(b"ok" if healthy else b"unhealthy")
    def log_message(self, *_args):
        pass

server = None
server_port = None
while True:
    desired_port = int(read_config().get("port", 0))
    if desired_port != server_port:
        if server is not None:
            server.shutdown()
            server.server_close()
        server = HTTPServer(("0.0.0.0", desired_port), Handler)
        server.timeout = 0.2
        threading.Thread(target=server.serve_forever, daemon=True).start()
        server_port = desired_port
    update_status(desired_port == forward_port)
    time.sleep(0.5)
