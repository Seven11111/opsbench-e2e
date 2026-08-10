from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
compose = os.environ.get("OPSBENCH_COMPOSE_BIN", "docker compose").split()
compose_file = str(case_dir / "environment/docker-compose.yaml")
subprocess.run(
    [*compose, "-f", compose_file, "exec", "-T", "db", "psql",
     "-v", "ON_ERROR_STOP=1", "-U", "opsbench", "-d", "app", "-c", 'CREATE INDEX IF NOT EXISTS orders_customer_id_idx ON orders(customer_id); ANALYZE orders;'],
    check=True,
)
