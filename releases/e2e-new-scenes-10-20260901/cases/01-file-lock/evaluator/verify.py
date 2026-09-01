from __future__ import annotations
import argparse
import json
import os
import shlex
import subprocess
import urllib.error
import urllib.request

TEMPLATE_ID = 'linux_file_lock_v1'
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
    def config():
        code, output, _ = target("cat /runtime/config.json")
        if code != 0:
            return {}
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {}
    cfg = config()
    checks = []
    probe_code, probe_out, probe_err = target("curl -fsS --max-time 3 http://127.0.0.1:8080/health")
    health = probe_code == 0
    detail = (probe_out or probe_err)[-500:]
    checks.append({"name": "business_operation", "passed": health, "weight": 0.35, "detail": detail})
    root_signal = False
    if TEMPLATE_ID == "linux_memory_growth_v1":
        root_signal = bool(cfg.get("growth_enabled"))
    elif TEMPLATE_ID == "linux_disk_full_v1":
        root_signal = target("test -f /data/filler && test $(df -Pk /data | awk 'NR==2 {print $4}') -lt 2048")[0] == 0
    elif TEMPLATE_ID == "linux_inode_exhaustion_v1":
        root_signal = target("test -d /data/inodes && test $(find /data/inodes -type f | wc -l) -ge 80")[0] == 0
    elif TEMPLATE_ID == "linux_upload_permission_v1":
        root_signal = target("test $(stat -c %a /data/uploads) = 555")[0] == 0
    elif TEMPLATE_ID == "linux_temp_permission_v1":
        root_signal = target("test $(stat -c %a /data/tmp) = 555")[0] == 0
    elif TEMPLATE_ID == "linux_file_lock_v1":
        root_signal = bool(cfg.get("lock_enabled"))
    elif TEMPLATE_ID == "app_stale_pid_v1":
        # The healthy service writes its own live PID at startup.  Only the
        # injected sentinel PID represents the stale-state fault.
        root_signal = bool(cfg.get("stale_pid")) or target("test -f /data/app.pid && test $(cat /data/app.pid) = 999999")[0] == 0
    elif TEMPLATE_ID == "http_upstream_timeout_v1":
        root_signal = int(cfg.get("delay_ms", 0)) > 100
    checks.append({"name": "root_signal_absent", "passed": not root_signal, "weight": 0.30, "detail": f"config={cfg}"})
    contract_ok = True
    if TEMPLATE_ID in {"linux_upload_permission_v1", "linux_temp_permission_v1"}:
        directory = "/data/uploads" if TEMPLATE_ID == "linux_upload_permission_v1" else "/data/tmp"
        code, output, _ = target(f"stat -c '%a %u' {directory}")
        contract_ok = code == 0 and output.startswith(("770", "1730")) and "777" not in output
    elif TEMPLATE_ID == "http_upstream_timeout_v1":
        contract_ok = int(cfg.get("delay_ms", 9999)) <= 100 and int(cfg.get("timeout_ms", 9999)) <= 500
    elif TEMPLATE_ID in {"linux_memory_growth_v1", "linux_file_lock_v1", "app_stale_pid_v1"}:
        contract_ok = cfg.get("repair_mode") in {"baseline", "persistent"}
    else:
        contract_ok = target("test -w /data")[0] == 0
    checks.append({"name": "repair_invariant", "passed": contract_ok, "weight": 0.20, "detail": "trusted runtime contract remains intact"})
    persistence = cfg.get("repair_mode") in {"baseline", "persistent"} and not root_signal
    checks.append({"name": "persistence", "passed": persistence, "weight": 0.15, "detail": "repair state is persistent and root signal is absent"})
    score = sum(item["weight"] for item in checks if item["passed"])
    # Critical checks are conjunctive.  Do not let floating point rounding or
    # a weighted partial score release a case with a failed invariant.
    result = {"passed": all(item["passed"] for item in checks), "score": round(score, 6), "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
