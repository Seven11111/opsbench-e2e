from __future__ import annotations

import json
import multiprocessing
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path("/runtime")
CONFIG = ROOT / "worker.conf"
STATUS = ROOT / "status.json"
worker = None


def busy_loop(work_units: int) -> None:
    while True:
        sum(index * index for index in range(work_units))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok\n")

    def log_message(self, *_args):
        pass


def read_config() -> dict:
    try:
        value = json.loads(CONFIG.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {"enabled": False, "work_units": 30000}
    except (OSError, json.JSONDecodeError):
        return {"enabled": False, "work_units": 30000}


def write_status(config: dict, healthy: bool) -> None:
    STATUS.write_text(
        json.dumps({
            "healthy": healthy,
            "enabled": bool(config.get("enabled")),
            "worker_alive": bool(worker and worker.is_alive()),
        }) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    global worker
    server = ThreadingHTTPServer(("0.0.0.0", 18081), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    while True:
        config = read_config()
        enabled = bool(config.get("enabled"))
        units = max(1000, min(100000, int(config.get("work_units", 30000))))
        if enabled and (worker is None or not worker.is_alive()):
            worker = multiprocessing.Process(target=busy_loop, args=(units,), daemon=True)
            worker.start()
        if not enabled and worker is not None:
            worker.terminate()
            worker.join(timeout=2)
            worker = None
        write_status(config, True)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
