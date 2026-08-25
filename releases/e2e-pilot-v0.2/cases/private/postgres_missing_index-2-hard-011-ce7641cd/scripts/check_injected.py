from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
compose = os.environ.get("OPSBENCH_COMPOSE_BIN", "docker compose").split()
compose_file = str(case_dir / "environment/docker-compose.yaml")
def psql(sql):
    result = subprocess.run(
        [*compose, "-f", compose_file, "exec", "-T", "db", "psql",
         "-At", "-U", "opsbench", "-d", "app", "-c", sql],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()
if psql("SELECT to_regclass('public.orders_customer_id_idx')"):
    raise SystemExit("injected index is still present")
plan = psql("EXPLAIN (FORMAT JSON) SELECT id, customer_id, payload FROM orders WHERE customer_id = 4242 ORDER BY id LIMIT 50")
if "Seq Scan" not in plan:
    raise SystemExit("injected sequential scan was not observed")
