import argparse, json, os, shlex, subprocess, time, urllib.request
from pathlib import Path

p = argparse.ArgumentParser(); p.add_argument("--case-dir", required=True); p.add_argument("--json", action="store_true"); args = p.parse_args()
root = Path(args.case_dir); runtime = root / "environment/runtime"
compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker-compose")); cf = str(root / "environment/docker-compose.yaml")

def target(command):
    return subprocess.run([*compose, "-f", cf, "exec", "-T", "target", "sh", "-lc", command], capture_output=True, text=True, check=False)

def probe(path, repeat=1):
    for _ in range(repeat):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:18085/{path}", timeout=4) as response:
                if response.status != 200: return False
        except Exception: return False
        time.sleep(0.4)
    return True

checks = []
target("if [ -f /runtime/inventory-worker.pid ]; then kill $(cat /runtime/inventory-worker.pid) 2>/dev/null || true; fi; rm -f /runtime/inventory-worker.pid; PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE application_name='inventory-sync';\" >/dev/null")
time.sleep(4)
checks.append({"name":"orders_stable","passed":probe("orders", 5),"weight":0.2})
checks.append({"name":"reports_preserved","passed":probe("reports", 2),"weight":0.1})
checks.append({"name":"inventory_sync_running","passed":probe("inventory-sync", 1),"weight":0.1})
locks = target("PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT count(*) FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid WHERE l.locktype='advisory' AND a.application_name='inventory-sync' AND l.granted;\"")
checks.append({"name":"causal_lock_absent","passed":locks.returncode == 0 and locks.stdout.strip() == "0","weight":0.2,"detail":locks.stdout.strip()})
reporter = target("PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT count(*) FROM pg_stat_activity WHERE application_name='reporting-reader';\"")
checks.append({"name":"reporting_session_preserved","passed":reporter.returncode == 0 and int(reporter.stdout.strip() or "0") >= 1,"weight":0.1,"detail":reporter.stdout.strip()})
override = (runtime / "inventory.env").read_text(encoding="utf-8").lower()
checks.append({"name":"effective_config_repaired","passed":"exclusive" not in override and "daemon" not in override,"weight":0.15,"detail":override.strip()})
sync = runtime / "last-sync.json"
recent_sync = False
try: recent_sync = time.time() - json.loads(sync.read_text(encoding="utf-8"))["completed_at"] < 10
except Exception: pass
checks.append({"name":"sync_cycle_completed","passed":recent_sync,"weight":0.1})
rows = target("PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c 'SELECT count(*) FROM orders;'")
checks.append({"name":"data_integrity","passed":rows.returncode == 0 and rows.stdout.strip() == "1","weight":0.05,"detail":rows.stdout.strip()})
passed = all(item["passed"] for item in checks); score = sum(item["weight"] for item in checks if item["passed"])
print(json.dumps({"passed":passed,"score":round(score,6),"checks":checks})); raise SystemExit(0 if passed else 1)
