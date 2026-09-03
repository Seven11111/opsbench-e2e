import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

COUNT = Path('/tmp/sink.received')
MODE = Path('/runtime/sink.mode')
COUNT.write_text('0\n', encoding='utf-8')
MODE.write_text('healthy\n', encoding='utf-8')
COUNT_LOCK = threading.Lock()

def fault_active():
    try:
        return MODE.read_text(encoding='utf-8').strip() == 'fault'
    except OSError:
        return False

def set_mode(value):
    MODE.write_text('fault\n' if value == 'fault' else 'healthy\n', encoding='utf-8')

def record_delivery():
    with COUNT_LOCK:
        try:
            current = int(COUNT.read_text(encoding='utf-8').strip() or '0')
        except (OSError, ValueError):
            current = 0
        COUNT.write_text(str(current + 1) + '\n', encoding='utf-8')

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/control'):
            mode = self.path.split('mode=', 1)[1].split('&', 1)[0] if 'mode=' in self.path else 'healthy'
            set_mode(mode)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'ok\n')
            return
        if self.path.startswith('/health'):
            try:
                delivered = int(COUNT.read_text(encoding='utf-8').strip() or '0')
            except (OSError, ValueError):
                delivered = 0
            body = json.dumps({'mode': 'fault' if fault_active() else 'healthy', 'delivered': delivered}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path.startswith('/control'):
            mode = self.path.split('mode=', 1)[1].split('&', 1)[0] if 'mode=' in self.path else 'healthy'
            set_mode(mode)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'ok\n')
            return
        length = int(self.headers.get('Content-Length', '0'))
        self.rfile.read(length)
        if fault_active():
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b'downstream unavailable\n')
            return
        record_delivery()
        self.send_response(204)
        self.end_headers()
    def log_message(self, *_args):
        pass

def serve_http():
    ThreadingHTTPServer(('0.0.0.0', 19880), Handler).serve_forever()

def serve_forward():
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 24224))
    server.listen(32)
    while True:
        conn, _ = server.accept()
        if fault_active():
            conn.close()
            continue
        recorded = False
        try:
            while True:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                if not recorded:
                    record_delivery()
                    recorded = True
        except OSError:
            pass
        finally:
            conn.close()

threading.Thread(target=serve_http, daemon=True).start()
serve_forward()
