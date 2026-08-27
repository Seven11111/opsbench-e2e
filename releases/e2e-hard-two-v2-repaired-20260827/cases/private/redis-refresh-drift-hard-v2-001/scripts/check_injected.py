from pathlib import Path
import json, os, shlex, subprocess, sys, time, urllib.error, urllib.request

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve(); compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker-compose")); cf = str(case_dir / "environment/docker-compose.yaml")
deadline = time.time() + 15
while time.time() < deadline:
    r = subprocess.run([*compose, "-f", cf, "exec", "-T", "target", "sh", "-lc", "redis-cli -h redis --raw GET catalog:active"], capture_output=True, text=True, check=False, timeout=30)
    try: injected = json.loads(r.stdout).get("version") == 1
    except Exception: injected = False
    failed = False
    try: urllib.request.urlopen("http://127.0.0.1:18087/catalog", timeout=4)
    except urllib.error.HTTPError as exc: failed = exc.code == 503
    except Exception: pass
    if injected and failed:
        raise SystemExit(0)
    time.sleep(0.5)
raise SystemExit("schema-v1 cache payload or catalog failure not observed")
