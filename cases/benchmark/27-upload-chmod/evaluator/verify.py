from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time

TEMPLATE_ID = "linux_upload_permission_v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    compose = shlex.split(
        os.environ.get(
            "OPSBENCH_COMPOSE_BIN",
            "docker-compose" if os.name == "nt" else "docker compose",
        )
    )
    compose_file = f"{args.case_dir}/environment/docker-compose.yaml"

    def target(command: str) -> tuple[int, str, str]:
        result = subprocess.run(
            [*compose, "-f", compose_file, "exec", "-T", "--user", "opsbench", "target", "sh", "-lc", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()

    def upload_status() -> int:
        result = target("curl -sS --max-time 3 -o /tmp/upload-response -w '%{http_code}' -X POST -d '{}' http://127.0.0.1:8080/upload")
        try:
            return int(result[1] or 0)
        except ValueError:
            return 0

    def permission_contract() -> bool:
        code, output, _ = target("stat -c '%a %u %g' /data/uploads")
        try:
            mode_text, uid_text, gid_text = output.split()[:3]
            mode, uid, gid = int(mode_text, 8), int(uid_text), int(gid_text)
        except (ValueError, TypeError):
            return False
        return code == 0 and uid == 10001 and gid == 10001 and bool(mode & 0o020) and not bool(mode & 0o002)

    health_code, health_out, health_err = target("curl -fsS --max-time 3 http://127.0.0.1:8080/health")
    status = upload_status()
    contract = permission_contract()
    checks = [
        {
            "name": "business_operation",
            "passed": health_code == 0 and status == 200,
            "weight": 0.35,
            "detail": f"health={(health_out or health_err)[-300:]} upload_status={status}",
        },
        {
            "name": "root_signal_absent",
            "passed": status == 200,
            "weight": 0.30,
            "detail": "live upload operation returns HTTP 200",
        },
        {
            "name": "repair_invariant",
            "passed": contract,
            "weight": 0.20,
            "detail": "service ownership is preserved, group write is enabled, and world write is absent",
        },
    ]
    restart = subprocess.run(
        [*compose, "-f", compose_file, "restart", "target"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    restart_ready = False
    for _ in range(10):
        restart_ready = restart.returncode == 0 and target("curl -fsS --max-time 3 http://127.0.0.1:8080/health")[0] == 0
        if restart_ready:
            break
        time.sleep(0.5)
    repeat_status = upload_status()
    persistence = restart_ready and repeat_status == 200 and permission_contract()
    checks.append(
        {
            "name": "persistence",
            "passed": persistence,
            "weight": 0.15,
            "detail": f"restart_returncode={restart.returncode} repeat_upload_status={repeat_status}",
        }
    )
    score = sum(item["weight"] for item in checks if item["passed"])
    result = {"passed": all(item["passed"] for item in checks), "score": round(score, 6), "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
