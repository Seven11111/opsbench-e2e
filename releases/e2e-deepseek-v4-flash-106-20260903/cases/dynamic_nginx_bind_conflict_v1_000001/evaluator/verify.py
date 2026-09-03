from __future__ import annotations
import argparse
import json
import os
import shlex
import subprocess
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
    target = subprocess.run(
        [*compose, "-f", compose_file, "exec", "-T", "target", "sh", "-lc",
         "pgrep -x nginx >/dev/null && ! pgrep -f '[p]ort_blocker.py' >/dev/null"],
        capture_output=True, text=True, check=False,
    )
    health = False
    try:
        with urllib.request.urlopen("http://127.0.0.1:18080/health", timeout=3) as response:
            health = response.status == 200
    except (OSError, urllib.error.URLError):
        pass
    checks = [
        {"name": "http_health", "passed": health, "weight": 0.5, "detail": "HTTP /health must return 200"},
        {"name": "process_state", "passed": target.returncode == 0, "weight": 0.5, "detail": "nginx is running and the port blocker is absent"},
    ]
    score = sum(item["weight"] for item in checks if item["passed"])
    result = {"passed": score >= 1.0, "score": round(score, 6), "checks": checks}
    print(json.dumps(result))
    return 0 if result["passed"] else 1
if __name__ == "__main__":
    raise SystemExit(main())
