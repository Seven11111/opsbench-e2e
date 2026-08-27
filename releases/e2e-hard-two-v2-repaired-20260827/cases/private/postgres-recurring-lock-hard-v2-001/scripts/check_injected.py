from pathlib import Path
import os, shlex, subprocess, sys, time, urllib.error, urllib.request

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker-compose"))
cf = str(case_dir / "environment/docker-compose.yaml")
query = "PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT count(*) FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid WHERE l.locktype='advisory' AND a.application_name='inventory-sync' AND l.granted;\""
deadline = time.time() + 15
last = ""
while time.time() < deadline:
    r = subprocess.run([*compose, "-f", cf, "exec", "-T", "target", "sh", "-lc", query], capture_output=True, text=True, check=False, timeout=30)
    last = r.stderr.strip() or r.stdout.strip()
    lock_present = r.returncode == 0 and int(r.stdout.strip() or "0") >= 1
    orders_failed = False
    try:
        urllib.request.urlopen("http://127.0.0.1:18085/orders", timeout=4)
    except urllib.error.HTTPError as exc:
        orders_failed = exc.code == 503
    except Exception:
        pass
    if lock_present and orders_failed:
        raise SystemExit(0)
    time.sleep(0.5)
raise SystemExit(f"injected lock or orders failure not observed: {last}")
