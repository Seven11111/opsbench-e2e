from __future__ import annotations
import argparse
import json
import os
import shlex
import subprocess
import time
import urllib.error
import urllib.request

TEMPLATE_ID = 'linux_temp_permission_v1'
HOST_PORT = 18090

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = args.case_dir
    compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker-compose" if os.name == "nt" else "docker compose"))
    compose_file = f"{root}/environment/docker-compose.yaml"
    def target(command):
        result = subprocess.run([*compose, "-f", compose_file, "exec", "-T", "--user", "opsbench", "target", "sh", "-lc", command], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    def upload_status():
        result = target("curl -sS --max-time 3 -o /tmp/upload-response -w '%{http_code}' -X POST -d '{}' http://127.0.0.1:8080/upload")
        try:
            return int(result[1] or 0)
        except ValueError:
            return 0
    def orders_probe():
        result = target("curl -sS --max-time 3 -o /tmp/orders-response -w '%{http_code} %{time_total}' http://127.0.0.1:8080/orders")
        parts = (result[1] or "").split()
        try:
            status = int(parts[0]) if parts else 0
            elapsed_ms = float(parts[1]) * 1000 if len(parts) > 1 else float('inf')
        except (ValueError, TypeError):
            status, elapsed_ms = 0, float('inf')
        return status, elapsed_ms
    def restart_target():
        result = subprocess.run([*compose, "-f", compose_file, "restart", "target"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, check=False)
        time.sleep(0.5)
        return result.returncode, result.stderr.strip()
    checks = []
    probe_code, probe_out, probe_err = target("curl -fsS --max-time 3 http://127.0.0.1:8080/health")
    health = probe_code == 0
    detail = (probe_out or probe_err)[-500:]
    checks.append({"name": "business_operation", "passed": health, "weight": 0.35, "detail": detail})
    root_signal = False
    if TEMPLATE_ID == "linux_memory_growth_v1":
        metrics_code, metrics_out, metrics_err = target("curl -fsS --max-time 3 http://127.0.0.1:8080/metrics")
        metrics = {}
        for line in metrics_out.splitlines():
            parts = line.split()
            if len(parts) == 2:
                try:
                    metrics[parts[0]] = float(parts[1])
                except ValueError:
                    pass
        growth_bytes = metrics.get("opsbench_memory_growth_bytes", float("inf"))
        memory_limit = metrics.get("opsbench_memory_limit_bytes", 0)
        growth_enabled = metrics.get("opsbench_memory_growth_enabled", 1)
        root_signal = metrics_code != 0 or growth_enabled > 0 or growth_bytes > memory_limit
    elif TEMPLATE_ID == "linux_disk_full_v1":
        root_signal = target("test -f /data/filler && test $(df -Pk /data | awk 'NR==2 {print $4}') -lt 2048")[0] == 0
    elif TEMPLATE_ID == "linux_inode_exhaustion_v1":
        root_signal = target("test -d /data/inodes && test $(find /data/inodes -type f | wc -l) -ge 80")[0] == 0
    elif TEMPLATE_ID == "linux_upload_permission_v1":
        root_signal = upload_status() != 200
    elif TEMPLATE_ID == "linux_temp_permission_v1":
        root_signal = target("test $(stat -c %a /data/tmp) = 555")[0] == 0
    elif TEMPLATE_ID == "linux_file_lock_v1":
        lock_probe = target("""python -c "import fcntl; h=open('/data/report.lock','a+'); fcntl.flock(h, fcntl.LOCK_EX|fcntl.LOCK_NB); fcntl.flock(h, fcntl.LOCK_UN)""")
        root_signal = lock_probe[0] != 0
    elif TEMPLATE_ID == "app_stale_pid_v1":
        # The healthy service writes its own live PID at startup.  Only the
        # injected sentinel PID represents the stale-state fault.
        root_signal = target("test -f /data/app.pid && test $(cat /data/app.pid) = 999999")[0] == 0
    elif TEMPLATE_ID == "http_upstream_timeout_v1":
        order_status, order_elapsed_ms = orders_probe()
        root_signal = order_status == 504 or order_status != 200 or order_elapsed_ms >= 600
    checks.append({"name": "root_signal_absent", "passed": not root_signal, "weight": 0.30, "detail": "live semantic root-signal probe"})
    contract_ok = True
    if TEMPLATE_ID in {"linux_upload_permission_v1", "linux_temp_permission_v1"}:
        directory = "/data/uploads" if TEMPLATE_ID == "linux_upload_permission_v1" else "/data/tmp"
        code, output, _ = target(f"stat -c '%a %u %g' {directory}")
        try:
            mode_text, uid_text, gid_text = output.split()[:3]
            mode, uid, gid = int(mode_text, 8), int(uid_text), int(gid_text)
        except (ValueError, TypeError):
            mode, uid, gid = 0, -1, -1
        if TEMPLATE_ID == "linux_upload_permission_v1":
            contract_ok = code == 0 and uid == 10001 and gid == 10001 and bool(mode & 0o020) and not bool(mode & 0o002)
        else:
            contract_ok = code == 0 and bool(mode & 0o010) and not bool(mode & 0o002)
    elif TEMPLATE_ID == "http_upstream_timeout_v1":
        order_status, order_elapsed_ms = orders_probe()
        contract_ok = order_status == 200 and order_elapsed_ms < 600
    elif TEMPLATE_ID == "linux_memory_growth_v1":
        contract_ok = metrics_code == 0 and memory_limit == 16 * 1024 * 1024 and growth_enabled == 0
    elif TEMPLATE_ID == "linux_file_lock_v1":
        if TEMPLATE_ID == "linux_file_lock_v1":
            contract_ok = target("""python -c "import fcntl; h=open('/data/report.lock','a+'); fcntl.flock(h, fcntl.LOCK_EX|fcntl.LOCK_NB); fcntl.flock(h, fcntl.LOCK_UN)""")[0] == 0
    elif TEMPLATE_ID == "app_stale_pid_v1":
        contract_ok = target("test -f /data/app.pid && test $(cat /data/app.pid) != 999999")[0] == 0
    else:
        contract_ok = target("test -w /data")[0] == 0
    checks.append({"name": "repair_invariant", "passed": contract_ok, "weight": 0.20, "detail": "trusted runtime contract remains intact"})
    if TEMPLATE_ID == "linux_memory_growth_v1":
        time.sleep(1)
        repeat_code, repeat_out, _ = target("curl -fsS --max-time 3 http://127.0.0.1:8080/metrics")
        repeat_values = {}
        for line in repeat_out.splitlines():
            parts = line.split()
            if len(parts) == 2:
                try:
                    repeat_values[parts[0]] = float(parts[1])
                except ValueError:
                    pass
        persistence = (
            repeat_code == 0
            and repeat_values.get("opsbench_memory_growth_enabled", 1) == 0
            and repeat_values.get("opsbench_memory_growth_bytes", float("inf")) <= repeat_values.get("opsbench_memory_limit_bytes", 0)
        )
    elif TEMPLATE_ID == "linux_upload_permission_v1":
        restart_code, restart_error = restart_target()
        restart_health = False
        for _ in range(10):
            restart_health = target("curl -fsS --max-time 3 http://127.0.0.1:8080/health")[0] == 0
            if restart_health:
                break
            time.sleep(0.5)
        persistence = restart_code == 0 and restart_health and upload_status() == 200 and contract_ok
    elif TEMPLATE_ID == "linux_file_lock_v1":
        time.sleep(0.5)
        persistence = target("""python -c "import fcntl; h=open('/data/report.lock','a+'); fcntl.flock(h, fcntl.LOCK_EX|fcntl.LOCK_NB); fcntl.flock(h, fcntl.LOCK_UN)""")[0] == 0
    elif TEMPLATE_ID == "http_upstream_timeout_v1":
        restart_code, restart_error = restart_target()
        restart_health = False
        for _ in range(10):
            restart_health = target("curl -fsS --max-time 3 http://127.0.0.1:8080/health")[0] == 0
            if restart_health:
                break
            time.sleep(0.5)
        repeat_status, repeat_elapsed_ms = orders_probe()
        persistence = restart_code == 0 and restart_health and repeat_status == 200 and repeat_elapsed_ms < 600 and contract_ok
    else:
        persistence = not root_signal
    checks.append({"name": "persistence", "passed": persistence, "weight": 0.15, "detail": "repair state is persistent and root signal is absent"})
    score = sum(item["weight"] for item in checks if item["passed"])
    # Critical checks are conjunctive.  Do not let floating point rounding or
    # a weighted partial score release a case with a failed invariant.
    result = {"passed": all(item["passed"] for item in checks), "score": round(score, 6), "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
