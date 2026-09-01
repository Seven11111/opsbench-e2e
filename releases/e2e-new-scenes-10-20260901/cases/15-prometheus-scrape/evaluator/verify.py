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

    config = (case_dir / 'environment/runtime/prometheus.yml').read_text()
    ready = subprocess.run(['curl', '-fsS', 'http://127.0.0.1:19090/-/ready'])
    scrape_up = False
    last_values = []
    for _ in range(15):
        query = subprocess.run(['curl', '-fsS', 'http://127.0.0.1:19090/api/v1/query?query=up%7Bjob%3D%22opsbench-target%22%7D'], capture_output=True, text=True)
        payload = json.loads(query.stdout) if query.returncode == 0 else {}
        last_values = payload.get('data', {}).get('result', [])
        scrape_up = bool(last_values and last_values[0].get('value', [None, '0'])[1] == '1')
        if scrape_up:
            break
        time.sleep(1)
    checks = [{"name": "scrape_up", "passed": scrape_up}, {"name": "service_health", "passed": ready.returncode == 0}, {"name": "effective_target", "passed": "exporter:19100" in config}, {"name": "persistence", "passed": "exporter:19100" in config}]
    for item in checks:
        item['weight'] = 1.0 / len(checks)
    passed = all(bool(item['passed']) for item in checks)
    result = {"passed": passed, "score": round(sum(bool(item["passed"]) for item in checks) / len(checks), 6), "checks": checks}
    print(json.dumps(result))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
