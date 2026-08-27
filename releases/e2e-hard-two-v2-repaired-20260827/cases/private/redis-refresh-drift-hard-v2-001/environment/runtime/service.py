import hashlib
import json
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RUNTIME = Path("/runtime")
WORKER = "/opt/opsbench/runtime/refresh_worker.py"


def redis_get(key: str) -> str:
    result = subprocess.run(["redis-cli", "-h", "redis", "--raw", "GET", key], capture_output=True, text=True, timeout=3, check=False)
    return result.stdout.strip()


def digest_items(items) -> str:
    body = json.dumps(items, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def worker_alive() -> bool:
    try:
        pid = int((RUNTIME / "refresh-worker.pid").read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def supervise_worker() -> None:
    while True:
        if not worker_alive():
            log_handle = open(RUNTIME / "refresh-worker.log", "a", encoding="utf-8")
            child = subprocess.Popen(["python", WORKER], stdout=log_handle, stderr=subprocess.STDOUT, start_new_session=True)
            (RUNTIME / "refresh-worker.pid").write_text(str(child.pid), encoding="utf-8")
        time.sleep(0.5)


def append_catalog_log(message: str) -> None:
    with (RUNTIME / "catalog.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{time.time():.3f} {message}\n")


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
            self.send(200, {"status": "ok", "refresh_worker_running": worker_alive()})
            return
        if self.path == "/catalog-preview":
            value = redis_get("catalog:preview")
            self.send(200 if value else 503, {"status": "ok" if value else "missing", "value": value})
            return
        if self.path == "/catalog":
            try:
                payload = json.loads(redis_get("catalog:active"))
                meta = json.loads(redis_get("catalog:meta"))
                items = payload.get("items")
                valid_items = isinstance(items, list) and bool(items) and all(
                    isinstance(item, dict)
                    and isinstance(item.get("id"), str)
                    and isinstance(item.get("price_cents"), int)
                    and item.get("currency") == "USD"
                    for item in items
                )
                ok = (
                    payload.get("version") == 2
                    and meta.get("schema_version") == 2
                    and valid_items
                    and meta.get("checksum") == digest_items(items)
                )
            except Exception:
                payload = {}; ok = False
            if ok:
                append_catalog_log("catalog payload accepted")
                self.send(200, {"status": "ok", "items": payload["items"]})
            else:
                append_catalog_log("catalog payload rejected: application contract mismatch")
                self.send(503, {"status": "unavailable", "error": "cache contract mismatch"})
            return
        self.send(404, {"error": "not found"})

    def log_message(self, *_args) -> None:
        return


if __name__ == "__main__":
    for path in (RUNTIME / "catalog.log", RUNTIME / "refresh-worker.log", RUNTIME / "audit.jsonl"):
        path.touch(exist_ok=True)
    threading.Thread(target=supervise_worker, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 18087), Handler).serve_forever()

