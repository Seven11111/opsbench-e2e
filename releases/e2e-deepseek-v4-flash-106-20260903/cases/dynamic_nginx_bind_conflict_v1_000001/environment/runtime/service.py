from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

ROOT = Path("/runtime")
NGINX_PREFIX = ROOT / "nginx-prefix"
NGINX_PID = ROOT / "nginx.pid"
FAULT = ROOT / "fault.json"
PROGRESS = ROOT / "fault_progress.json"
STATUS = ROOT / "status.json"
CONFIG = ROOT / "nginx.conf"


def read_json(path: Path, default: dict) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else dict(default)
    except (OSError, json.JSONDecodeError):
        return dict(default)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def pid_alive(path: Path) -> bool:
    try:
        pid = int(path.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def stop_nginx() -> None:
    subprocess.run(["nginx", "-s", "stop", "-c", str(CONFIG), "-p", str(NGINX_PREFIX)], check=False)
    for _ in range(10):
        if not pid_alive(NGINX_PID):
            return
        time.sleep(0.2)


def start_nginx() -> bool:
    NGINX_PREFIX.mkdir(parents=True, exist_ok=True)
    test = subprocess.run(
        ["nginx", "-t", "-c", str(CONFIG), "-p", str(NGINX_PREFIX)],
        capture_output=True, text=True, check=False,
    )
    if test.returncode != 0:
        (ROOT / "nginx-error.log").write_text(
            (test.stderr or test.stdout or "nginx -t failed")[-12000:],
            encoding="utf-8",
        )
        return False
    subprocess.run(["nginx", "-c", str(CONFIG), "-p", str(NGINX_PREFIX)], check=False)
    return pid_alive(NGINX_PID)


def socket_health() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 18080), timeout=0.5):
            return True
    except OSError:
        return False


def main() -> None:
    blocker = None
    progress = read_json(PROGRESS, {"blocker_spawned": False})
    while True:
        fault = read_json(FAULT, {"mode": "baseline"})
        mode = str(fault.get("mode") or "baseline")
        if mode == "bind_conflict":
            if not progress.get("blocker_spawned"):
                stop_nginx()
                blocker = subprocess.Popen(["python", "/opt/opsbench/port_blocker.py", "18080"])
                progress["blocker_spawned"] = True
                progress["blocker_pid"] = blocker.pid
                write_json(PROGRESS, progress)
            blocker_alive = bool(blocker and blocker.poll() is None)
            if not blocker_alive and not pid_alive(NGINX_PID):
                start_nginx()
            elif blocker_alive:
                stop_nginx()
            healthy = (not blocker_alive) and pid_alive(NGINX_PID) and socket_health()
        else:
            if blocker and blocker.poll() is None:
                blocker.send_signal(signal.SIGTERM)
            if not pid_alive(NGINX_PID):
                start_nginx()
            healthy = pid_alive(NGINX_PID) and socket_health()
        write_json(STATUS, {
            "healthy": healthy,
            "mode": mode,
            "nginx_pid_alive": pid_alive(NGINX_PID),
        })
        time.sleep(0.5)


if __name__ == "__main__":
    main()
