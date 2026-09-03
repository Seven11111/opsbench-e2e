import json
import time
from pathlib import Path

path = Path("/runtime/status.json")
deadline = time.time() + 10
while time.time() < deadline:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        value = {}
    if value.get("fault_active") is True:
        raise SystemExit(0)
    time.sleep(0.2)
raise SystemExit("injected fault is not observable")
