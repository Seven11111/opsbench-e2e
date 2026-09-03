from __future__ import annotations
import argparse
import json
import os
import shlex
import subprocess
import time
import urllib.error
import urllib.request

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = args.case_dir
    compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker compose"))
    compose_file = f"{root}/environment/docker-compose.yaml"
    try:
        with open(f"{root}/environment/runtime/worker.conf", encoding="utf-8") as handle:
            config = json.load(handle)
    except (OSError, json.JSONDecodeError):
        config = {}
    container = subprocess.run(
        [*compose, "-f", compose_file, "ps", "-q", "target"],
        capture_output=True, text=True, check=False,
    ).stdout.strip()
    samples = []
    if container:
        for _ in range(4):
            raw = subprocess.run(
                [os.environ.get("OPSBENCH_DOCKER_BIN", "docker"), "stats", "--no-stream", "--format", "{{.CPUPerc}}", container],
                capture_output=True, text=True, check=False,
            ).stdout.strip().rstrip("%")
            try:
                samples.append(float(raw))
            except ValueError:
                pass
            time.sleep(0.5)
    cpu_ok = bool(samples) and max(samples) < 20.0
    health = False
    try:
        with urllib.request.urlopen("http://127.0.0.1:18081/health", timeout=3) as response:
            health = response.status == 200
    except (OSError, urllib.error.URLError):
        pass
    process = subprocess.run(
        [*compose, "-f", compose_file, "exec", "-T", "target", "sh", "-lc", "! pgrep -f '[b]usy_loop' >/dev/null"],
        capture_output=True, text=True, check=False,
    )
    checks = [
        {"name": "cpu_sample", "passed": cpu_ok and not bool(config.get("enabled")), "weight": 0.4, "detail": f"samples={samples}"},
        {"name": "process_state", "passed": process.returncode == 0, "weight": 0.2, "detail": "runaway worker is absent"},
        {"name": "service_health", "passed": health, "weight": 0.4, "detail": "HTTP /health must return 200"},
    ]
    score = sum(item["weight"] for item in checks if item["passed"])
    result = {"passed": score >= 1.0, "score": round(score, 6), "checks": checks}
    print(json.dumps(result))
    return 0 if result["passed"] else 1
if __name__ == "__main__":
    raise SystemExit(main())
