import json, time
from pathlib import Path
p=Path("/runtime/fault.json")
p.write_text(json.dumps({"mode": 'injected', "repair_mode": ""})+"\n", encoding="utf-8")
time.sleep(1)
