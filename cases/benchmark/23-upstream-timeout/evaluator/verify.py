from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time

TEMPLATE_ID = "http_upstream_timeout_v1"


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

    def orders_probe() -> tuple[int, float]:
        code, output, _ = target(
            "curl -sS --max-time 3 -o /tmp/orders-response -w '%{http_code} %{time_total}' http://127.0.0.1:8080/orders"
        )
        parts = output.split()
        try:
            return int(parts[0]), float(parts[1]) * 1000 if len(parts) > 1 else float("inf")
        except (ValueError, TypeError, IndexError):
            return (0 if code != 0 else 200), float("inf")

    def service_ready() -> bool:
        return target("curl -fsS --max-time 3 http://127.0.0.1:8080/health")[0] == 0

    health_code, health_out, health_err = target("curl -fsS --max-time 3 http://127.0.0.1:8080/health")
    order_status, order_elapsed_ms = orders_probe()
    business_ok = health_code == 0 and order_status == 200 and order_elapsed_ms < 600
    root_absent = order_status == 200 and order_elapsed_ms < 600
    checks = [
        {
            "name": "business_operation",
            "passed": business_ok,
            "weight": 0.35,
            "detail": f"health={(health_out or health_err)[-300:]} orders_status={order_status} elapsed_ms={order_elapsed_ms:.1f}",
        },
        {
            "name": "root_signal_absent",
            "passed": root_absent,
            "weight": 0.30,
            "detail": "live order probe is successful within the public latency objective",
        },
        {
            "name": "repair_invariant",
            "passed": business_ok,
            "weight": 0.20,
            "detail": "the public order contract remains healthy; no timeout-budget state is inspected",
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
        restart_ready = restart.returncode == 0 and service_ready()
        if restart_ready:
            break
        time.sleep(0.5)
    repeat_status, repeat_elapsed_ms = orders_probe()
    persistence = restart_ready and repeat_status == 200 and repeat_elapsed_ms < 600
    checks.append(
        {
            "name": "persistence",
            "passed": persistence,
            "weight": 0.15,
            "detail": f"restart_returncode={restart.returncode} repeat_status={repeat_status} repeat_elapsed_ms={repeat_elapsed_ms:.1f}",
        }
    )
    score = sum(item["weight"] for item in checks if item["passed"])
    result = {"passed": all(item["passed"] for item in checks), "score": round(score, 6), "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
