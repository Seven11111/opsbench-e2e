from __future__ import annotations

import fcntl
import http.server
import json
import base64
import os
import signal
import socket
import subprocess
import threading
import time
import urllib.parse
from pathlib import Path

ROOT = Path("/runtime")
CONFIG = ROOT / "config.json"
DATA = Path("/data")
LOCK = DATA / "report.lock"
PID = DATA / "app.pid"
PORT = 8080
_memory = []
_lock_process = None


def read_config() -> dict:
    try:
        value = json.loads(CONFIG.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_pid() -> None:
    try:
        PID.write_text(str(os.getpid()) + "\n", encoding="utf-8")
    except OSError:
        pass


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def writable(path: Path) -> bool:
    probe = path / ".opsbench-write-probe"
    try:
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def free_bytes(path: Path) -> int:
    return int(os.statvfs(path).f_bavail * os.statvfs(path).f_frsize)


def free_inodes(path: Path) -> int:
    return int(os.statvfs(path).f_favail)


def lock_holder() -> None:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        while read_config().get("lock_enabled", False):
            time.sleep(0.25)


def maintain_fault_state() -> None:
    global _memory, _lock_process
    while True:
        cfg = read_config()
        if cfg.get("growth_enabled", False):
            if len(_memory) < 48:
                _memory.append(bytearray(1024 * 1024))
        else:
            _memory.clear()
        if cfg.get("lock_enabled", False):
            if _lock_process is None or _lock_process.poll() is not None:
                _lock_process = subprocess.Popen(["python", "-c", "from pathlib import Path; import fcntl,time; p=Path('/data/report.lock'); p.touch(); h=p.open('a+'); fcntl.flock(h.fileno(), fcntl.LOCK_EX); time.sleep(3600)"])
        elif _lock_process is not None and _lock_process.poll() is None:
            _lock_process.terminate()
            _lock_process = None
        time.sleep(0.25)


def current_health() -> tuple[bool, str]:
    cfg = read_config()
    mode = str(cfg.get("mode", "baseline"))
    if mode == "memory_growth":
        return (not bool(cfg.get("growth_enabled", False)), "memory growth is disabled")
    if mode == "disk_full":
        ok = free_bytes(DATA) >= int(cfg.get("minimum_free_bytes", 2 * 1024 * 1024)) and writable(DATA)
        return (ok, "filesystem has writable headroom")
    if mode == "inode_exhaustion":
        ok = free_inodes(DATA) >= int(cfg.get("minimum_free_inodes", 16)) and writable(DATA)
        return (ok, "filesystem has free inodes")
    if mode == "upload_permission":
        return (writable(DATA / "uploads"), "upload directory is writable")
    if mode == "temp_permission":
        return (writable(DATA / "tmp"), "temporary directory is writable")
    if mode == "file_lock":
        try:
            with LOCK.open("a+") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return True, "report lock is available"
        except (OSError, BlockingIOError):
            return False, "report lock is held by another process"
    if mode == "stale_pid":
        stale = bool(cfg.get("stale_pid", False))
        return (not stale and writable(DATA), "application PID state is valid")
    if mode == "upstream_timeout":
        delay = int(cfg.get("delay_ms", 0))
        budget = int(cfg.get("timeout_ms", 500))
        return (delay <= 100 and delay <= budget, "dependency latency is inside the service budget")
    return True, "baseline service is healthy"


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        cfg = read_config()
        if self.path == "/health":
            healthy, detail = current_health()
            self.send_json(200 if healthy else 503, {"healthy": healthy, "detail": detail})
            return
        if self.path == "/report":
            healthy, detail = current_health()
            self.send_json(200 if healthy else 409, {"healthy": healthy, "detail": detail, "mode": cfg.get("mode")})
            return
        if self.path == "/orders":
            delay = int(cfg.get("delay_ms", 0))
            budget = int(cfg.get("timeout_ms", 500))
            time.sleep(min(delay, 1500) / 1000.0)
            if delay > budget:
                self.send_json(504, {"error": "upstream timeout", "delay_ms": delay, "timeout_ms": budget})
            else:
                self.send_json(200, {"orders": ["order-001"], "delay_ms": delay})
            return
        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path in {"/upload", "/temp"}:
            target = DATA / ("uploads" if self.path == "/upload" else "tmp")
            try:
                target.mkdir(parents=True, exist_ok=True)
                (target / "request.txt").write_text("request\n", encoding="utf-8")
                self.send_json(200, {"accepted": True})
            except OSError as exc:
                self.send_json(500, {"accepted": False, "error": str(exc)})
            return
        self.send_json(404, {"error": "not found"})


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    write_pid()
    threading.Thread(target=maintain_fault_state, daemon=True).start()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    def stop(_sig, _frame):
        server.shutdown()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
