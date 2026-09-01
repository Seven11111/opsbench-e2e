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

    config = (case_dir / 'environment/runtime/fluent-bit.conf').read_text()
    health_ok = False
    metrics_ok = False
    for _ in range(12):
        health_ok = http_ok('http://127.0.0.1:19202/api/v1/health')
        metrics_ok = http_ok('http://127.0.0.1:19202/api/v1/metrics')
        if health_ok and metrics_ok:
            break
        time.sleep(1)
    checks = [{"name": "service_health", "passed": health_ok}, {"name": "effective_output", "passed": "Host         sink" in config and "missing-sink" not in config}, {"name": "metrics_available", "passed": metrics_ok}, {"name": "persistence", "passed": "Host         sink" in config}]
    for item in checks:
        item['weight'] = 1.0 / len(checks)
    passed = all(bool(item['passed']) for item in checks)
    result = {"passed": passed, "score": round(sum(bool(item["passed"]) for item in checks) / len(checks), 6), "checks": checks}
    print(json.dumps(result))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
