from __future__ import annotations
import json
import sys
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
config = json.loads((case_dir / "environment" / "runtime" / "config.json").read_text(encoding="utf-8"))
expected = {'runaway': True, 'work_units': 50000}
if config != expected:
    raise SystemExit("injection check failed")

import os
import shlex
import subprocess
import time

def _cpu_sample():
    compose_bin = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker compose"))
    compose_file = str(case_dir / "environment" / "docker-compose.yaml")
    container = subprocess.run(
        [*compose_bin, "-f", compose_file, "ps", "-q", "target"],
        capture_output=True, text=True, timeout=10, check=False,
    ).stdout.strip()
    if not container:
        return None
    docker_bin = [compose_bin[0]] if compose_bin else ["docker"]
    raw = subprocess.run(
        [*docker_bin, "stats", "--no-stream", "--format", "{{.CPUPerc}}", container],
        capture_output=True, text=True, timeout=10, check=False,
    ).stdout.strip().rstrip("%").strip()
    return float(raw) if raw else None

samples = []
for _ in range(4):
    try:
        value = _cpu_sample()
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        value = None
        samples.append(str(exc))
    if value is not None:
        samples.append(value)
        if value >= 20.0:
            break
    time.sleep(1)
if not any(isinstance(value, (int, float)) and value >= 20.0 for value in samples):
    raise SystemExit(f"injected CPU fault was not observed: {samples!r}")


(case_dir / "environment" / "runtime" / "status.json").write_text(json.dumps({"healthy": False}, indent=2), encoding="utf-8")
