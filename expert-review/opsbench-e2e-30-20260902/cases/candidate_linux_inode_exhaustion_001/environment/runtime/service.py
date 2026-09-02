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
# Fault switches are benchmark control state, not application-observable
# configuration. Keep them outside the Agent's public working directory.
INTERNAL_ROOT = Path("/var/lib/opsbench/internal")
CONFIG = INTERNAL_ROOT / "config.json"
DATA = Path("/data")
LOCK = DATA / "report.lock"
PID = DATA / "app.pid"
PORT = 8080
_memory = []
_lock_process = None
MEMORY_LIMIT_BYTES = 16 * 1024 * 1024


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


def service_writable(path: Path) -> bool:
    """Model write access for the declared application identity."""
    try:
        stat = path.stat()
        mode = stat.st_mode
        if stat.st_uid == 10001 and mode & 0o200:
            return True
        if stat.st_gid == 10001 and mode & 0o020:
            return True
        return bool(mode & 0o002)
    except OSError:
        return False


def prepare_lock_file() -> None:
    """Keep the observable lock probe writable by the service identity."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.touch(exist_ok=True)
    os.chmod(LOCK, 0o666)


def free_bytes(path: Path) -> int:
    return int(os.statvfs(path).f_bavail * os.statvfs(path).f_frsize)


def free_inodes(path: Path) -> int:
    return int(os.statvfs(path).f_favail)


def ensure_access_directories() -> None:
    """Recreate runtime directories without erasing an injected fault.

    The case uses a tmpfs for /data, so a target restart can recreate the
    directory entries.  The private fault marker makes that restart
    deterministic: a restart preserves the injected bad mode, while a
    repaired state restores the declared application identity and mode.
    """
    cfg = read_config()
    for name, baseline_mode in (("uploads", 0o770), ("tmp", 0o1730)):
        path = DATA / name
        path.mkdir(parents=True, exist_ok=True)
        if cfg.get("repair_mode") == "fault" and cfg.get("mode") in {"upload_permission", "temp_permission"}:
            os.chmod(path, 0o555)
            continue
        uid = 10001
        gid = 10001
        os.chown(path, uid, gid)
        os.chmod(path, baseline_mode)


def memory_metrics() -> dict:
    """Expose the live resource signal used by the memory case.

    The metric is derived from the allocated worker buffer, not from the
    private configuration flag alone.  The flag controls whether the fault
    producer is active; the verifier and Agent can observe the resulting
    bytes, limit, and growth state through the public endpoint.
    """
    cfg = read_config()
    return {
        "memory_growth_bytes": len(_memory) * 1024 * 1024,
        "memory_limit_bytes": int(cfg.get("memory_limit_bytes", MEMORY_LIMIT_BYTES)),
        "memory_growth_enabled": bool(cfg.get("growth_enabled", False)),
    }


def lock_holder() -> None:
    prepare_lock_file()
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
                _lock_process = subprocess.Popen(["python", "-c", "from pathlib import Path; import fcntl,time; p=Path('/data/report.lock'); p.touch(); p.chmod(0o666); h=p.open('a+'); fcntl.flock(h.fileno(), fcntl.LOCK_EX); time.sleep(3600)"])
        elif _lock_process is not None and _lock_process.poll() is None:
            _lock_process.terminate()
            _lock_process = None
        time.sleep(0.25)


def current_health() -> tuple[bool, str]:
    cfg = read_config()
    mode = str(cfg.get("mode", "baseline"))
    if mode == "memory_growth":
        metrics = memory_metrics()
        healthy = metrics["memory_growth_bytes"] <= metrics["memory_limit_bytes"] and not metrics["memory_growth_enabled"]
        return (healthy, f"worker memory is {metrics['memory_growth_bytes']} bytes of {metrics['memory_limit_bytes']} bytes")
    if mode == "disk_full":
        ok = free_bytes(DATA) >= int(cfg.get("minimum_free_bytes", 2 * 1024 * 1024)) and writable(DATA)
        return (ok, "filesystem has writable headroom")
    if mode == "inode_exhaustion":
        ok = free_inodes(DATA) >= int(cfg.get("minimum_free_inodes", 16)) and writable(DATA)
        return (ok, "filesystem has free inodes")
    if mode == "upload_permission":
        return (service_writable(DATA / "uploads"), "upload directory is writable")
    if mode == "temp_permission":
        return (service_writable(DATA / "tmp"), "temporary directory is writable")
    if mode == "file_lock":
        try:
            prepare_lock_file()
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
            self.send_json(200 if healthy else 409, {"healthy": healthy, "detail": detail})
            return
        if self.path == "/metrics":
            metrics = memory_metrics()
            lines = [
                f"opsbench_memory_growth_bytes {metrics['memory_growth_bytes']}",
                f"opsbench_memory_limit_bytes {metrics['memory_limit_bytes']}",
                f"opsbench_memory_growth_enabled {int(metrics['memory_growth_enabled'])}",
            ]
            data = ("\n".join(lines) + "\n").encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
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
        if self.path == "/opsbench/control":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length) or b"{}")
                action = str(payload.get("action", "")).strip().lower()
            except (ValueError, TypeError, json.JSONDecodeError):
                self.send_json(400, {"ok": False, "error": "invalid control request"})
                return
            cfg = read_config()
            if action == "restore":
                cfg.update(repair_mode="persistent")
                if cfg.get("mode") == "memory_growth":
                    cfg["growth_enabled"] = False
                elif cfg.get("mode") == "file_lock":
                    cfg["lock_enabled"] = False
                elif cfg.get("mode") == "stale_pid":
                    cfg["stale_pid"] = False
                    PID.unlink(missing_ok=True)
                elif cfg.get("mode") == "upstream_timeout":
                    cfg.update(delay_ms=20, timeout_ms=500)
                elif cfg.get("mode") == "upload_permission":
                    os.chown(DATA / "uploads", 10001, 10001)
                    os.chmod(DATA / "uploads", 0o770)
                    cfg["fault_active"] = False
                elif cfg.get("mode") == "temp_permission":
                    os.chown(DATA / "tmp", 10001, 10001)
                    os.chmod(DATA / "tmp", 0o1730)
                    cfg["fault_active"] = False
                elif cfg.get("mode") == "disk_full":
                    (DATA / "filler").unlink(missing_ok=True)
                elif cfg.get("mode") == "inode_exhaustion":
                    import shutil
                    shutil.rmtree(DATA / "inodes", ignore_errors=True)
            elif action == "temporary_capacity" and cfg.get("mode") == "memory_growth":
                cfg.update(memory_limit_bytes=64 * 1024 * 1024, repair_mode="temporary")
            elif action == "raise_timeout_budget" and cfg.get("mode") == "upstream_timeout":
                cfg.update(timeout_ms=2000, repair_mode="wrong-contract")
            else:
                self.send_json(400, {"ok": False, "error": "unsupported bounded repair action"})
                return
            CONFIG.write_text(json.dumps(cfg), encoding="utf-8")
            self.send_json(200, {"ok": True, "healthy": current_health()[0], "action": action})
            return
        if self.path in {"/upload", "/temp"}:
            target = DATA / ("uploads" if self.path == "/upload" else "tmp")
            try:
                if not service_writable(target):
                    raise PermissionError(f"service account cannot write to {target}")
                target.mkdir(parents=True, exist_ok=True)
                (target / "request.txt").write_text("request\n", encoding="utf-8")
                self.send_json(200, {"accepted": True})
            except PermissionError as exc:
                self.send_json(403, {"accepted": False, "error": str(exc)})
            except OSError as exc:
                self.send_json(500, {"accepted": False, "error": str(exc)})
            return
        self.send_json(404, {"error": "not found"})


def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    ensure_access_directories()
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
