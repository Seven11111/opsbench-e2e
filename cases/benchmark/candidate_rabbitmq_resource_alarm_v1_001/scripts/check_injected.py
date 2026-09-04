import os
import shlex
import subprocess
from pathlib import Path

root = Path(__file__).parents[1]
compose = [*shlex.split(os.environ.get('OPSBENCH_COMPOSE_BIN', 'docker-compose' if os.name == 'nt' else 'docker compose')), '-f', str(root / 'environment/docker-compose.yaml')]
result = subprocess.run([*compose, 'exec', '-T', 'rabbitmq', 'rabbitmq-diagnostics', '-q', 'alarms'], capture_output=True, text=True)
if result.returncode != 0 or not result.stdout.strip():
    raise SystemExit(result.stderr or 'RabbitMQ disk alarm was not injected')
