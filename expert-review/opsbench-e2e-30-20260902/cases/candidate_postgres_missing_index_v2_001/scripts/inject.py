from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
compose = os.environ.get("OPSBENCH_COMPOSE_BIN", "docker compose").split()
compose_file = str(case_dir / "environment/docker-compose.yaml")
command = [
    *compose, "-f", compose_file, "exec", "-T", "db", "psql",
    "-v", "ON_ERROR_STOP=1", "-U", "opsbench", "-d", "app", "-c", 'DROP INDEX IF EXISTS orders_customer_id_idx; ANALYZE orders;',
]
last = None
for attempt in range(20):
    last = subprocess.run(command, capture_output=True, text=True, check=False)
    if last.returncode == 0:
        break
    # PostgreSQL may still be completing recovery or the large fixture's
    # initialization when Compose reports the container healthy.  Retry only
    # connection/setup failures; the final error remains visible to Runner.
    if attempt + 1 < 20:
        import time
        time.sleep(2)
if last is None or last.returncode != 0:
    raise SystemExit((last.stderr if last is not None else "psql setup failed").strip())
