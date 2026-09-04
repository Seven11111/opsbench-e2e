from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import time


def query(url: str) -> dict:
    result = subprocess.run(
        ["curl", "-fsS", url],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        return {}
    try:
        value = json.loads(result.stdout)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def active_target_healthy(instance: str) -> bool:
    payload = query("http://127.0.0.1:19090/api/v1/targets?state=active")
    for target in payload.get("data", {}).get("activeTargets", []):
        labels = target.get("labels", {})
        if labels.get("job") == "opsbench-target" and labels.get("instance") == instance:
            return str(target.get("health") or "").lower() == "up"
    return False


def scrape_state() -> tuple[bool, bool, list[dict]]:
    up_payload = query("http://127.0.0.1:19090/api/v1/query?query=up%7Bjob%3D%22opsbench-target%22%2Cinstance%3D%22exporter%3A19100%22%7D")
    up_values = up_payload.get("data", {}).get("result", [])
    scrape_up = active_target_healthy("exporter:19100")
    metric_payload = query("http://127.0.0.1:19090/api/v1/query?query=opsbench_target_up")
    metric_values = metric_payload.get("data", {}).get("result", [])
    target_metric = bool(metric_values and metric_values[0].get("value", [None, "0"])[1] == "1")
    return scrape_up, target_metric, up_values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    case_dir = os.path.abspath(args.case_dir)
    compose = shlex.split(
        os.environ.get(
            "OPSBENCH_COMPOSE_BIN",
            "docker-compose" if os.name == "nt" else "docker compose",
        )
    )
    compose_file = os.path.join(case_dir, "environment", "docker-compose.yaml")

    ready = subprocess.run(
        ["curl", "-fsS", "http://127.0.0.1:19090/-/ready"],
        capture_output=True,
        text=True,
        check=False,
    )
    scrape_up = False
    target_metric = False
    last_values: list[dict] = []
    for _ in range(15):
        scrape_up, target_metric, last_values = scrape_state()
        if scrape_up and target_metric:
            break
        time.sleep(1)

    checks = [
        {"name": "scrape_up", "passed": scrape_up, "weight": 0.25},
        {"name": "service_health", "passed": ready.returncode == 0, "weight": 0.20},
        {"name": "effective_target", "passed": scrape_up and target_metric, "weight": 0.30},
    ]

    # The task promises restart persistence.  Verify the actual Prometheus
    # process lifecycle rather than treating a second query as persistence.
    restart = subprocess.run(
        [*compose, "-f", compose_file, "restart", "prometheus"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    restart_ready = False
    restart_scrape = False
    restart_metric = False
    for _ in range(15):
        ready_after = subprocess.run(
            ["curl", "-fsS", "http://127.0.0.1:19090/-/ready"],
            capture_output=True,
            text=True,
            check=False,
        )
        restart_scrape, restart_metric, _ = scrape_state()
        restart_ready = ready_after.returncode == 0
        if restart_ready and restart_scrape and restart_metric:
            break
        time.sleep(1)
    checks.append(
        {
            "name": "persistence",
            "passed": restart.returncode == 0 and restart_ready and restart_scrape and restart_metric,
            "weight": 0.25,
            "detail": f"restart_returncode={restart.returncode} ready={restart_ready} scrape_up={restart_scrape} target_metric={restart_metric}",
        }
    )
    passed = all(bool(item["passed"]) for item in checks)
    score = sum(item["weight"] for item in checks if item["passed"])
    result = {
        "passed": passed,
        "score": round(score, 6),
        "checks": checks,
        "last_target_values": last_values,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
