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

    compose = [*shlex.split(os.environ.get('OPSBENCH_COMPOSE_BIN', 'docker-compose' if os.name == 'nt' else 'docker compose')), '-f', str(case_dir / 'environment/docker-compose.yaml')]
    alarm = subprocess.run([*compose, 'exec', '-T', 'rabbitmq', 'rabbitmq-diagnostics', '-q', 'alarms'], capture_output=True, text=True)
    ping = subprocess.run([*compose, 'exec', '-T', 'rabbitmq', 'rabbitmq-diagnostics', '-q', 'ping'], capture_output=True, text=True)
    overview = subprocess.run([*compose, 'exec', '-T', 'rabbitmq', 'rabbitmqctl', 'list_queues'], capture_output=True, text=True)
    alarm_ok = alarm.returncode == 0 and ('no alarms' in alarm.stdout.lower() or 'reported no alarms' in alarm.stdout.lower())
    checks = [{"name": "alarm_cleared", "passed": alarm_ok}, {"name": "service_health", "passed": ping.returncode == 0}, {"name": "message_flow", "passed": overview.returncode == 0}, {"name": "persistence", "passed": alarm_ok}]
    for item in checks:
        item['weight'] = 1.0 / len(checks)
    passed = all(bool(item['passed']) for item in checks)
    result = {"passed": passed, "score": round(sum(bool(item["passed"]) for item in checks) / len(checks), 6), "checks": checks}
    print(json.dumps(result))
    return 0 if passed else 1

if __name__ == '__main__':
    raise SystemExit(main())
