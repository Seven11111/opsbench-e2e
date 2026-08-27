import json
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RUNTIME = Path("/runtime")
WORKER = "/opt/opsbench/runtime/inventory_worker.py"
LOG = RUNTIME / "orders.log"


def append_log(message: str) -> None:
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{time.time():.3f} {message}\n")


def psql(sql: str, *, app_name: str, timeout: int = 5) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PGPASSWORD"] = "opsbench-local-only"
    env["PGAPPNAME"] = app_name
    return subprocess.run(
        ["psql", "-h", "db", "-U", "opsbench", "-d", "app", "-At", "-c", sql],
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def worker_alive() -> bool:
    pid_path = RUNTIME / "inventory-worker.pid"
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def supervise_worker() -> None:
    while True:
        if not worker_alive():
            log_handle = open(RUNTIME / "inventory-worker.log", "a", encoding="utf-8")
            child = subprocess.Popen(
                ["python", WORKER],
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            (RUNTIME / "inventory-worker.pid").write_text(str(child.pid), encoding="utf-8")
        time.sleep(0.5)


class Handler(BaseHTTPRequestHandler):
    def send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send(200, {"status": "ok", "worker_running": worker_alive()})
            return
        if self.path == "/orders":
            query = psql(
                "SET statement_timeout=900; SELECT pg_advisory_xact_lock(424242); SELECT count(*) FROM orders;",
                app_name="orders-api",
                timeout=3,
            )
            if query.returncode == 0:
                append_log("orders request completed")
                self.send(200, {"status": "ok", "count": int(query.stdout.strip().splitlines()[-1])})
            else:
                append_log("orders request failed: statement timeout while acquiring operational lock")
                self.send(503, {"status": "unavailable", "error": "database statement timeout"})
            return
        if self.path == "/reports":
            query = psql("SELECT count(*) FROM orders;", app_name="reports-api", timeout=3)
            self.send(200 if query.returncode == 0 else 503, {"status": "ok" if query.returncode == 0 else "failed"})
            return
        if self.path == "/inventory-sync":
            self.send(200 if worker_alive() else 503, {"status": "running" if worker_alive() else "stopped"})
            return
        self.send(404, {"error": "not found"})

    def log_message(self, *_args) -> None:
        return


if __name__ == "__main__":
    for path in (LOG, RUNTIME / "inventory-worker.log", RUNTIME / "audit.jsonl"):
        path.touch(exist_ok=True)
    threading.Thread(target=supervise_worker, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 18085), Handler).serve_forever()

