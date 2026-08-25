from __future__ import annotations
import os
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker compose"))
compose_file = str(case_dir / "environment/docker-compose.yaml")
for _ in range(20):
    try:
        with urllib.request.urlopen("http://127.0.0.1:18080/health", timeout=2) as response:
            if response.status == 200:
                time.sleep(0.5)
                continue
    except (OSError, urllib.error.URLError):
        break
    time.sleep(0.5)
else:
    raise SystemExit("injected HTTP endpoint unexpectedly healthy")
result = subprocess.run(
    [*compose, "-f", compose_file, "exec", "-T", "target", "sh", "-lc", "ss -ltnp | grep ':18080 '"],
    capture_output=True, text=True, check=False,
)
if result.returncode != 0:
    raise SystemExit("injected port blocker was not observed")
