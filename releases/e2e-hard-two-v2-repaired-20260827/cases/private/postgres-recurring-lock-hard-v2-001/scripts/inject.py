from pathlib import Path
import json, os, shlex, subprocess, sys, time

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
runtime = case_dir / "environment/runtime"
compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker-compose"))
cf = str(case_dir / "environment/docker-compose.yaml")

def target(command):
    result = subprocess.run(
        [*compose, "-f", cf, "exec", "-T", "target", "sh", "-lc", command],
        capture_output=True, text=True, check=False, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"target command failed: {command}")
    return result

(runtime / "inventory.env").write_text("lock_mode=exclusive\ntransaction_scope=daemon\n", encoding="utf-8")
(runtime / "state.json").write_text(json.dumps({"mode": "injected", "fault": "recurring_lock"}, indent=2) + "\n", encoding="utf-8")
target("PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE application_name='inventory-sync';\" >/dev/null")
target("if [ -f /runtime/inventory-worker.pid ]; then kill $(cat /runtime/inventory-worker.pid) 2>/dev/null || true; fi; rm -f /runtime/inventory-worker.pid")
time.sleep(4)
