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

(runtime / "inventory.env").write_text("", encoding="utf-8")
(runtime / "orders.log").write_text("", encoding="utf-8")
(runtime / "audit.jsonl").write_text("", encoding="utf-8")
(runtime / "state.json").write_text(json.dumps({"mode": "baseline"}, indent=2) + "\n", encoding="utf-8")
target("PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE application_name IN ('inventory-sync','reporting-reader');\" >/dev/null")
target("if [ -f /runtime/inventory-worker.pid ]; then kill $(cat /runtime/inventory-worker.pid) 2>/dev/null || true; fi; rm -f /runtime/inventory-worker.pid")
target("nohup env PGPASSWORD=opsbench-local-only PGAPPNAME=reporting-reader psql -h db -U opsbench -d app -c 'SELECT pg_advisory_lock(909090); SELECT pg_sleep(3600);' >/tmp/reporting-reader.log 2>&1 </dev/null &")
deadline = time.time() + 10
while time.time() < deadline:
    check = target("PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT 1 FROM pg_stat_activity WHERE datname='app' AND application_name='reporting-reader' LIMIT 1;\"")
    if check.stdout.strip() == "1":
        break
    time.sleep(0.5)
else:
    raise RuntimeError("reporting-reader session was not established")
