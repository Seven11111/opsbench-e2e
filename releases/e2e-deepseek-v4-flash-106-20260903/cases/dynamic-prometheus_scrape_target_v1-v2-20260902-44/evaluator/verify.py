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

    def query(promql):
        encoded = promql.replace('{', '%7B').replace('}', '%7D').replace('=', '%3D').replace('"', '%22')
        result = subprocess.run(
            ['curl', '-fsS', 'http://127.0.0.1:19090/api/v1/query?query=' + encoded],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            return {}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {}

    def gauge_value(payload):
        values = payload.get('data', {}).get('result', []) if isinstance(payload, dict) else []
        return float(values[0].get('value', [None, 'nan'])[1]) if values else float('nan')

    def active_target_healthy(instance):
        result = subprocess.run(
            ['curl', '-fsS', 'http://127.0.0.1:19090/api/v1/targets?state=active'],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            return False
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return False
        for target in payload.get('data', {}).get('activeTargets', []):
            labels = target.get('labels', {})
            if labels.get('job') == 'opsbench-target' and labels.get('instance') == instance:
                return str(target.get('health') or '').lower() == 'up'
        return False

    compose = [*shlex.split(os.environ.get('OPSBENCH_COMPOSE_BIN', 'docker-compose' if os.name == 'nt' else 'docker compose')), '-f', str(case_dir / 'environment/docker-compose.yaml')]
    target_query = 'up{job="opsbench-target",instance="exporter:19100"}'

    ready = subprocess.run(['curl', '-fsS', 'http://127.0.0.1:19090/-/ready'], check=False)
    scrape_up = False
    target_metric = False
    for _ in range(15):
        scrape_up = active_target_healthy('exporter:19100')
        target_metric = gauge_value(query('opsbench_target_up')) == 1.0
        if scrape_up and target_metric:
            break
        time.sleep(1)
    checks = [
        {"name": "scrape_up", "passed": scrape_up},
        {"name": "service_health", "passed": ready.returncode == 0},
        {"name": "effective_target", "passed": scrape_up and target_metric},
        {"name": "persistence", "passed": False},
    ]
    restart = subprocess.run(
        [*compose, 'restart', 'prometheus'],
        capture_output=True, text=True, check=False, timeout=60,
    )
    restart_ready = False
    restart_scrape = False
    restart_metric = False
    for _ in range(15):
        ready_after = subprocess.run(['curl', '-fsS', 'http://127.0.0.1:19090/-/ready'], check=False)
        restart_ready = ready_after.returncode == 0
        restart_scrape = active_target_healthy('exporter:19100')
        restart_metric = gauge_value(query('opsbench_target_up')) == 1.0
        if restart_ready and restart_scrape and restart_metric:
            break
        time.sleep(1)
    checks[-1] = {"name": "persistence", "passed": restart.returncode == 0 and restart_ready and restart_scrape and restart_metric}
    for item in checks:
        item['weight'] = 1.0 / len(checks)
    passed = all(bool(item['passed']) for item in checks)
    result = {"passed": passed, "score": round(sum(bool(item["passed"]) for item in checks) / len(checks), 6), "checks": checks}
    print(json.dumps(result))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
