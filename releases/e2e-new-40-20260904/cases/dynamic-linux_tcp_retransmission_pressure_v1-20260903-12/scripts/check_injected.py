import json, time
from pathlib import Path
p=Path("/runtime/status.json")
deadline=time.time()+10
while time.time()<deadline:
    try: value=json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError): value={}
    if value.get("fault_active") is True: raise SystemExit(0)
    time.sleep(.2)
raise SystemExit("injected fault is not observable")
