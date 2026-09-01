from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time

TEMPLATE_ID = "linux_memory_growth_v1"


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

    def metrics() -> tuple[int, dict[str, float], str]:
        code, output, error = target("curl -fsS --max-time 3 http://127.0.0.1:8080/metrics")
        values: dict[str, float] = {}
        for line in output.splitlines():
            parts = line.split()
            if len(parts) == 2:
                try:
                    values[parts[0]] = float(parts[1])
                except ValueError:
                    continue
        return code, values, error

    health_code, health_out, health_err = target("curl -fsS --max-time 3 http://127.0.0.1:8080/health")
    metrics_code, current, metrics_err = metrics()
    growth = current.get("opsbench_memory_growth_bytes", float("inf"))
    limit = current.get("opsbench_memory_limit_bytes", 0)
    enabled = current.get("opsbench_memory_growth_enabled", 1)
    root_absent = metrics_code == 0 and enabled == 0 and growth <= limit
    checks = [
        {
            "name": "business_operation",
            "passed": health_code == 0,
            "weight": 0.35,
            "detail": (health_out or health_err)[-500:],
        },
        {
            "name": "root_signal_absent",
            "passed": root_absent,
            "weight": 0.30,
            "detail": "live metrics show growth disabled and usage within the declared limit",
        },
        {
            "name": "repair_invariant",
            "passed": metrics_code == 0 and limit == 16 * 1024 * 1024 and enabled == 0,
            "weight": 0.20,
            "detail": "memory limit and workload contract remain intact",
        },
    ]
    time.sleep(1)
    repeat_code, repeat, repeat_err = metrics()
    repeat_growth = repeat.get("opsbench_memory_growth_bytes", float("inf"))
    repeat_limit = repeat.get("opsbench_memory_limit_bytes", 0)
    repeat_enabled = repeat.get("opsbench_memory_growth_enabled", 1)
    checks.append(
        {
            "name": "persistence",
            "passed": repeat_code == 0 and repeat_enabled == 0 and repeat_growth <= repeat_limit,
            "weight": 0.15,
            "detail": "repeated live metrics remain within budget after observation",
        }
    )
    score = sum(item["weight"] for item in checks if item["passed"])
    result = {"passed": all(item["passed"] for item in checks), "score": round(score, 6), "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
