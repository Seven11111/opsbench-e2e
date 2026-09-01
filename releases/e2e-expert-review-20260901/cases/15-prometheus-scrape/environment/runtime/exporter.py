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
    def log_message(self, *_args):
        pass

HTTPServer(('0.0.0.0', 19100), Handler).serve_forever()
