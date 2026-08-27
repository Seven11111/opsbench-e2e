import json
import os
import subprocess
import time
from pathlib import Path

RUNTIME = Path("/runtime")


def effective_config() -> dict:
    config = json.loads((RUNTIME / "base_config.json").read_text(encoding="utf-8"))
    override = RUNTIME / "inventory.env"
    if override.exists():
        for line in override.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip().lower()] = value.strip()
    return config


def run_psql(sql: str, app_name: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PGPASSWORD"] = "opsbench-local-only"
    env["PGAPPNAME"] = app_name
    return subprocess.run(
        ["psql", "-h", "db", "-U", "opsbench", "-d", "app", "-At", "-c", sql],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


while True:
    config = effective_config()
    if config.get("lock_mode") == "exclusive" or config.get("transaction_scope") == "daemon":
        run_psql("SELECT pg_advisory_lock(424242); SELECT pg_sleep(3600);", "inventory-sync")
        time.sleep(0.5)
    else:
        run_psql(
            "BEGIN; SELECT pg_advisory_xact_lock(424242); SELECT count(*) FROM orders; COMMIT;",
            "inventory-sync-cycle",
        )
        (RUNTIME / "last-sync.json").write_text(
            json.dumps({"completed_at": time.time(), "mode": "transaction"}),
            encoding="utf-8",
        )
        time.sleep(2)

