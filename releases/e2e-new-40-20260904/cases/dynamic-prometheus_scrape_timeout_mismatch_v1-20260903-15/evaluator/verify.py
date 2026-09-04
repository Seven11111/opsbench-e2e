import json, os, time, urllib.request, urllib.error
from pathlib import Path
target=os.environ.get("OPSBENCH_TARGET_URL", "http://127.0.0.1:8080").rstrip("/")
def get(path):
    try:
        with urllib.request.urlopen(target+path, timeout=4) as r: return r.status, json.loads(r.read().decode())
    except (OSError, ValueError, urllib.error.URLError): return 0, {}
try: profile=json.loads(Path("/etc/opsbench/profile.json").read_text(encoding="utf-8"))
except (OSError, ValueError): profile={}
state={}
deadline=time.time()+2.0
while time.time()<deadline:
    try:
        state=json.loads(Path("/runtime/status.json").read_text(encoding="utf-8"))
        if state: break
    except (OSError, ValueError):
        pass
    time.sleep(0.05)
code, business=get("/business")
checks=[
 {"name":"business_operation", "passed": code==200 and bool(business.get("healthy")), "weight":.35, "detail":str(code)},
 {"name":"mechanism_signal_absent", "passed": not bool(state.get("fault_active")) and int(state.get("signal_value",1))==0 and state.get("signal_reading")==profile.get("healthy_value"), "weight":.30, "detail":str(state)},
 {"name":"repair_invariant", "passed": state.get("mode") in {"baseline","repaired"} and state.get("mechanism")==profile.get("mechanism"), "weight":.20, "detail":"profile-bound live capability state"},
 {"name":"persistence", "passed": state.get("mode") in {"baseline","repaired"} and (state.get("mode")=="baseline" or state.get("repair_mode")=="persistent"), "weight":.15, "detail":"persistent repair state"},
]
result={"passed":all(item["passed"] for item in checks),"score":round(sum(item["weight"] for item in checks if item["passed"]),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result["passed"] else 1)
