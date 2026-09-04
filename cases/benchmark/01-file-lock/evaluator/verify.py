from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time

TEMPLATE_ID = "linux_file_lock_v1"


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

    def lock_available() -> bool:
        return target(
            'python -c "import fcntl; h=open(\'/data/report.lock\',\'a+\'); fcntl.flock(h, fcntl.LOCK_EX|fcntl.LOCK_NB); fcntl.flock(h, fcntl.LOCK_UN)"'
        )[0] == 0

    health_code, health_out, health_err = target("curl -fsS --max-time 3 http://127.0.0.1:8080/health")
    checks = [
        {
            "name": "business_operation",
            "passed": health_code == 0,
            "weight": 0.35,
            "detail": (health_out or health_err)[-500:],
        },
        {
            "name": "root_signal_absent",
            "passed": lock_available(),
            "weight": 0.30,
            "detail": "live lock acquisition probe; no internal control state is read",
        },
        {
            "name": "repair_invariant",
            "passed": lock_available(),
            "weight": 0.20,
            "detail": "report-processing lock contract remains usable",
        },
    ]
    time.sleep(0.5)
    checks.append(
        {
            "name": "persistence",
            "passed": lock_available(),
            "weight": 0.15,
            "detail": "live lock acquisition remains available after observation",
        }
    )
    score = sum(item["weight"] for item in checks if item["passed"])
    result = {"passed": all(item["passed"] for item in checks), "score": round(score, 6), "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
