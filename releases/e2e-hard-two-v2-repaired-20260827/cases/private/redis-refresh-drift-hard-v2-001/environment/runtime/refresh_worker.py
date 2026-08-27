import hashlib
import json
import subprocess
import time
from pathlib import Path

RUNTIME = Path("/runtime")


def read_env(path: Path) -> dict:
    values = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1); values[key.strip().lower()] = value.strip()
    return values


def config() -> dict:
    base = json.loads((RUNTIME / "refresh-base.json").read_text(encoding="utf-8"))
    return {**base, **read_env(RUNTIME / "refresh.env")}


def redis(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["redis-cli", "-h", "redis", *args], capture_output=True, text=True, timeout=4, check=False)


def refresh() -> None:
    current = config(); version = int(current.get("schema_version", 2)); ttl = int(current.get("ttl_sec", 30))
    if version == 2:
        items = [{"id": "sku-1", "price_cents": 1299, "currency": "USD"}]
    else:
        items = [{"sku": "sku-1", "price": "12.99"}]
    checksum = hashlib.sha256(json.dumps(items, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    payload = json.dumps({"version": version, "items": items}, separators=(",", ":"))
    meta = json.dumps({"schema_version": version, "checksum": checksum, "generated_at": time.time()}, separators=(",", ":"))
    redis("SETEX", "catalog:active", str(ttl), payload)
    redis("SETEX", "catalog:meta", str(ttl), meta)
    (RUNTIME / "last-refresh.json").write_text(json.dumps({"completed_at": time.time(), "schema_version": version, "ttl_sec": ttl}), encoding="utf-8")
    print(f"refresh completed schema_version={version} ttl={ttl}", flush=True)


last_trigger = ""
while True:
    refresh()
    interval = max(1, int(config().get("refresh_interval_sec", 3)))
    deadline = time.time() + interval
    while time.time() < deadline:
        trigger = RUNTIME / "refresh.trigger"
        value = trigger.read_text(encoding="utf-8") if trigger.exists() else ""
        if value and value != last_trigger:
            last_trigger = value
            break
        time.sleep(0.2)

