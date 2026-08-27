import argparse, hashlib, json, os, shlex, subprocess, time, urllib.request
from pathlib import Path

p = argparse.ArgumentParser(); p.add_argument("--case-dir", required=True); p.add_argument("--json", action="store_true"); args = p.parse_args()
root = Path(args.case_dir); runtime = root / "environment/runtime"; compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker-compose")); cf = str(root / "environment/docker-compose.yaml")
def target(command): return subprocess.run([*compose, "-f", cf, "exec", "-T", "target", "sh", "-lc", command], capture_output=True, text=True, check=False)
def redis(command): return target(f"redis-cli -h redis --raw {command}")
def probe(path, repeat=1):
    for _ in range(repeat):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:18087/{path}", timeout=4) as response:
                if response.status != 200: return False
        except Exception: return False
        time.sleep(0.4)
    return True

checks = []
target("if [ -f /runtime/refresh-worker.pid ]; then kill $(cat /runtime/refresh-worker.pid) 2>/dev/null || true; fi; rm -f /runtime/refresh-worker.pid")
time.sleep(7)
checks.append({"name":"catalog_stable","passed":probe("catalog", 5),"weight":0.2})
checks.append({"name":"preview_preserved","passed":probe("catalog-preview", 2) and redis("GET catalog:preview").stdout.strip() == "preview-ok","weight":0.1})
payload_raw = redis("GET catalog:active").stdout.strip(); meta_raw = redis("GET catalog:meta").stdout.strip()
contract_ok = False
try:
    payload = json.loads(payload_raw); meta = json.loads(meta_raw); items = payload.get("items")
    checksum = hashlib.sha256(json.dumps(items, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    contract_ok = payload.get("version") == 2 and meta.get("schema_version") == 2 and meta.get("checksum") == checksum and all(isinstance(x.get("price_cents"), int) and x.get("currency") == "USD" for x in items)
except Exception: pass
checks.append({"name":"schema_and_checksum","passed":contract_ok,"weight":0.25,"detail":payload_raw})
ttl_active = redis("TTL catalog:active"); ttl_meta = redis("TTL catalog:meta")
try: ttl_ok = 1 <= int(ttl_active.stdout.strip()) <= 30 and 1 <= int(ttl_meta.stdout.strip()) <= 30
except Exception: ttl_ok = False
checks.append({"name":"ttl_preserved","passed":ttl_ok,"weight":0.1,"detail":[ttl_active.stdout.strip(),ttl_meta.stdout.strip()]})
override = (runtime / "refresh.env").read_text(encoding="utf-8").lower()
checks.append({"name":"effective_config_repaired","passed":"schema_version=1" not in override,"weight":0.15,"detail":override.strip()})
last = runtime / "last-refresh.json"; worker_ok = False
try: worker_ok = time.time() - json.loads(last.read_text(encoding="utf-8"))["completed_at"] < 5
except Exception: pass
checks.append({"name":"refresh_worker_persistent","passed":worker_ok,"weight":0.15})
catalog_base = json.loads((runtime / "catalog-base.json").read_text(encoding="utf-8"))
checks.append({"name":"validation_preserved","passed":catalog_base.get("validation_enabled") is True,"weight":0.05})
passed = all(item["passed"] for item in checks); score = sum(item["weight"] for item in checks if item["passed"])
print(json.dumps({"passed":passed,"score":round(score,6),"checks":checks})); raise SystemExit(0 if passed else 1)
