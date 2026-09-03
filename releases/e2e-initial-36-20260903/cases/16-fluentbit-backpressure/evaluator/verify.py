from __future__ import annotations
import argparse
import json
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case-dir', required=True)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    case_dir = Path(args.case_dir).resolve()
    import os
    import shlex
    import time
    import urllib.request

    def http_ok(url):
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(url, timeout=5) as response:
                response.read(4096)
            return True
        except Exception:
            return False

    compose = [*shlex.split(os.environ.get('OPSBENCH_COMPOSE_BIN', 'docker-compose' if os.name == 'nt' else 'docker compose')), '-f', str(case_dir / 'environment/docker-compose.yaml')]
    def sink_count():
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open('http://127.0.0.1:19980/health', timeout=5) as response:
                payload = json.load(response)
            return int(payload.get('delivered', 0) or 0)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return 0

    health_ok = http_ok('http://127.0.0.1:19202/api/v1/health')
    metrics_ok = http_ok('http://127.0.0.1:19202/api/v1/metrics')
    baseline_count = sink_count()
    delivery_count = baseline_count
    for _ in range(10):
        try:
            request = urllib.request.Request('http://127.0.0.1:19880/', data=b'{"message":"verify"}', headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(request, timeout=5).read(1000)
        except Exception:
            pass
        time.sleep(1)
        delivery_count = sink_count()
        if delivery_count > baseline_count:
            break
    effective_output = delivery_count > baseline_count or baseline_count > 0
    persistent_delivery = effective_output
    restart_result = subprocess.run([*compose, 'restart', 'fluent-bit'], capture_output=True, text=True, check=False, timeout=30)
    restart_ok = restart_result.returncode == 0
    time.sleep(3)
    delivery_after_restart = delivery_count
    for _ in range(10):
        try:
            request = urllib.request.Request('http://127.0.0.1:19880/', data=b'{"message":"repeat"}', headers={'Content-Type': 'application/json'})
            urllib.request.urlopen(request, timeout=5).read(1000)
        except Exception:
            pass
        time.sleep(1)
        delivery_after_restart = sink_count()
        if delivery_after_restart > delivery_count:
            break
    persistent_delivery = persistent_delivery and restart_ok and delivery_after_restart > max(delivery_count, baseline_count)
    checks = [{"name": "service_health", "passed": health_ok and restart_ok}, {"name": "effective_output", "passed": effective_output, "detail": f"delivered_before={baseline_count}, delivered_after_probe={delivery_count}"}, {"name": "metrics_available", "passed": metrics_ok}, {"name": "persistence", "passed": persistent_delivery, "detail": f"delivered_after_restart={delivery_after_restart}"}]
    for item in checks:
        item['weight'] = 1.0 / len(checks)
    passed = all(bool(item['passed']) for item in checks)
    result = {"passed": passed, "score": round(sum(bool(item["passed"]) for item in checks) / len(checks), 6), "checks": checks}
    print(json.dumps(result))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
