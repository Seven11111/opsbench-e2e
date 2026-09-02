from __future__ import annotations
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
config = (case_dir / "environment/runtime/worker.conf").read_text(encoding="utf-8")
if '"enabled": true' not in config.lower():
    raise SystemExit("injected worker configuration was not enabled")
compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker compose"))
compose_file = str(case_dir / "environment/docker-compose.yaml")
container = subprocess.run(
    [*compose, "-f", compose_file, "ps", "-q", "target"],
    capture_output=True, text=True, check=False,
).stdout.strip()
if not container:
    raise SystemExit("target container not found")
samples = []
docker_bin = os.environ.get("OPSBENCH_DOCKER_BIN", "docker")
for _ in range(5):
    raw = subprocess.run(
        [docker_bin, "stats", "--no-stream", "--format", "{{.CPUPerc}}", container],
        capture_output=True, text=True, check=False,
    ).stdout.strip().rstrip("%")
    if raw:
        samples.append(float(raw))
    if samples and samples[-1] >= 20:
        break
    time.sleep(0.5)
if not samples or max(samples) < 20:
    raise SystemExit(f"injected CPU pressure was not observed: {samples!r}")
