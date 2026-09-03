from __future__ import annotations

import http.server
import json
import os
import signal
import socket
import subprocess
import threading
import time
from pathlib import Path

ROOT = Path("/runtime")
PROFILE_PATH = Path("/etc/opsbench/profile.json")
FAULT_PATH = ROOT / "fault.json"
STATUS_PATH = ROOT / "status.json"
DATA = Path("/data")
DATA.mkdir(exist_ok=True)
STATE_LOCK = threading.Lock()
RESOURCE_LOCK = threading.RLock()
STATE: dict = {}
HELD_FILE = None
SOCKETS: list = []
CHILDREN: list = []


def read_json(path: Path, default: dict) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else dict(default)
    except (OSError, json.JSONDecodeError):
        return dict(default)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def synchronized(function):
    def wrapper(*args, **kwargs):
        with RESOURCE_LOCK:
            return function(*args, **kwargs)
    return wrapper


@synchronized
def close_resources() -> None:
    global HELD_FILE
    if HELD_FILE is not None:
        try:
            HELD_FILE.close()
        except OSError:
            pass
        HELD_FILE = None
    while SOCKETS:
        try:
            left, right = SOCKETS.pop()
            for sock in (left, right):
                sock.close()
        except OSError:
            pass
    while CHILDREN:
        child = CHILDREN.pop()
        try:
            child.terminate()
            child.wait(timeout=1)
        except (OSError, subprocess.SubprocessError):
            pass
    for path in (DATA / "deleted-open.log", DATA / "write-probe", DATA / "mount-probe"):
        try:
            path.unlink()
        except OSError:
            pass
    for path, mode in ((DATA / "mount-probe", 0o664), (DATA / "write-probe", 0o770)):
        try:
            path.touch(exist_ok=True)
            path.chmod(mode)
        except OSError:
            pass


def fault_state() -> dict:
    profile = read_json(PROFILE_PATH, {})
    fault = read_json(FAULT_PATH, {"mode": "baseline"})
    mode = str(fault.get("mode") or "baseline")
    return profile, fault, mode


@synchronized
def reconcile() -> None:
    global STATE, HELD_FILE, SOCKETS, CHILDREN
    profile, fault, mode = fault_state()
    injected = mode not in {"baseline", "repaired"}
    mechanism = str(profile.get("mechanism") or "unknown")
    if not injected:
        close_resources()
    elif mechanism == "unlinked_inode_held_by_process" and HELD_FILE is None:
        path = DATA / "deleted-open.log"
        path.write_text("held open\n", encoding="utf-8")
        HELD_FILE = path.open("a+", encoding="utf-8")
        path.unlink(missing_ok=True)
    elif mechanism == "stateful_connection_table_pressure" and not SOCKETS:
        SOCKETS = [socket.socketpair() for _ in range(12)]
    elif mechanism == "supervisor_restart_policy":
        if not CHILDREN or CHILDREN[0].poll() is not None:
            CHILDREN = [subprocess.Popen(["sh", "-c", "exit 1"])]
    elif mechanism == "pids_cgroup_limit" and not CHILDREN:
        CHILDREN = [subprocess.Popen(["sleep", "30"]) for _ in range(8)]
    elif mechanism == "filesystem_write_protection":
        try:
            (DATA / "mount-probe").touch(exist_ok=True)
            (DATA / "mount-probe").chmod(0o444 if injected else 0o664)
        except OSError:
            pass
    elif mechanism == "bind_mount_identity_mismatch":
        try:
            (DATA / "write-probe").touch(exist_ok=True)
            (DATA / "write-probe").chmod(0o555 if injected else 0o770)
        except OSError:
            pass
    signal_value = 1 if injected else 0
    if mechanism == "supervisor_restart_policy":
        signal_value = len(CHILDREN) if injected else 0
    if mechanism == "pids_cgroup_limit":
        signal_value = len(CHILDREN) if injected else 0
    if mechanism == "stateful_connection_table_pressure":
        signal_value = len(SOCKETS) if injected else 0
    STATE = {
        "healthy": not injected,
        "fault_active": injected,
        "mode": mode,
        "mechanism": mechanism,
        "mechanism_signal": str(profile.get("signal") or "mechanism_signal"),
        "signal_value": signal_value,
        "resource_class": profile.get("resource"),
        "observability": profile.get("observability"),
        "repair_surface": profile.get("repair"),
        "repair_mode": str(fault.get("repair_mode") or ("persistent" if mode == "repaired" else "")),
        "write_path": "/data/write-probe",
        "rootfs_policy": "read_only",
        "updated_at": time.time(),
    }
    with STATE_LOCK:
        write_json(STATUS_PATH, STATE)


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        return

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        reconcile()
        if self.path == "/metrics":
            lines = [
                f"opsbench_fault_active {int(STATE.get('fault_active', True))}",
                f"opsbench_signal_value {int(STATE.get('signal_value', 1))}",
                f"opsbench_{STATE.get('mechanism_signal', 'mechanism_signal')} {int(STATE.get('signal_value', 1))}",
            ]
            body = ("\n".join(lines) + "\n").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path in {"/health", "/business"}:
            status = 200 if STATE.get("healthy") else 503
            self.send_json(status, {"healthy": bool(STATE.get("healthy")), "operation": self.path[1:]})
            return
        if self.path == "/opsbench/state":
            self.send_json(200, dict(STATE))
            return
        self.send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/opsbench/control":
            self.send_json(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, TypeError):
            payload = {}
        action = str(payload.get("action") or "")
        if action not in {"restore", "restore_service_state", "repair_observed_fault"}:
            self.send_json(400, {"healthy": False, "error": "only the bounded observed-state repair is accepted"})
            return
        write_json(FAULT_PATH, {"mode": "repaired", "repair_mode": "persistent"})
        reconcile()
        self.send_json(200, {"healthy": True, "action": "restore", "state_owner": "target-service"})


def main() -> None:
    write_json(STATUS_PATH, {"healthy": True, "fault_active": False, "mode": "baseline"})
    reconcile()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    def refresh_state() -> None:
        # Fault injection is performed by a separate lifecycle process. Keep
        # the observable state synchronized even when no probe request arrives
        # between injection and check_injected.
        while True:
            reconcile()
            time.sleep(0.2)
    threading.Thread(target=refresh_state, name="opsbench-state-refresh", daemon=True).start()
    def stop_server(*_args) -> None:
        close_resources()
        # BaseServer.shutdown() must run outside the serve_forever thread.
        threading.Thread(target=server.shutdown, name="opsbench-shutdown", daemon=True).start()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, stop_server)
    server.serve_forever()


if __name__ == "__main__":
    main()
