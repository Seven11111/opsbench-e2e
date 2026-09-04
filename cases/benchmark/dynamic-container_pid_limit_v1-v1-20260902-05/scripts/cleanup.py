from pathlib import Path
import json
import time

path = Path("/runtime/fault.json")
if not path.parent.exists():
    # The lifecycle scripts are also invoked by the host-side failure path.
    # There is no container-mounted /runtime directory in that context.
    raise SystemExit(0)
payload = {"mode": 'baseline', "repair_mode": ""}
path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
time.sleep(1.0)
