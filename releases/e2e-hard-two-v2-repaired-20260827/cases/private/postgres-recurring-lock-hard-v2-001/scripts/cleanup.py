from pathlib import Path
import json, os, shlex, subprocess, sys

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
runtime = case_dir / "environment/runtime"
compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker-compose"))
cf = str(case_dir / "environment/docker-compose.yaml")
(runtime / "inventory.env").write_text("", encoding="utf-8")
(runtime / "state.json").write_text(json.dumps({"mode": "baseline"}, indent=2) + "\n", encoding="utf-8")
subprocess.run([*compose, "-f", cf, "exec", "-T", "target", "sh", "-lc", "PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE application_name IN ('inventory-sync','reporting-reader');\" >/dev/null; if [ -f /runtime/inventory-worker.pid ]; then kill $(cat /runtime/inventory-worker.pid) 2>/dev/null || true; fi; rm -f /runtime/inventory-worker.pid"], capture_output=True, text=True, check=False, timeout=30)
