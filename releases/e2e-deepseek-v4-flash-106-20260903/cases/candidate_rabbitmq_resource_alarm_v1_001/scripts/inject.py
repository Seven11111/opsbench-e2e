import os
import shlex
import subprocess
from pathlib import Path

root = Path(__file__).parents[1]
compose = [*shlex.split(os.environ.get('OPSBENCH_COMPOSE_BIN', 'docker-compose' if os.name == 'nt' else 'docker compose')), '-f', str(root / 'environment/docker-compose.yaml')]
# Docker Desktop's free space is larger than 100GB; use a threshold above it
# so the injection deterministically raises a disk resource alarm.
subprocess.run([*compose, 'exec', '-T', 'rabbitmq', 'rabbitmqctl', 'set_disk_free_limit', '2000000000000'], check=True)
