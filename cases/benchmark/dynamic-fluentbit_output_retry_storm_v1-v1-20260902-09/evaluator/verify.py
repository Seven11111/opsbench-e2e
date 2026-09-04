from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

TARGET_URL = os.environ.get("OPSBENCH_TARGET_URL", "http://127.0.0.1:8080").rstrip("/")


def get(path: str):
    try:
        with urllib.request.urlopen(TARGET_URL + path, timeout=4) as response:
            return response.status, json.loads(response.read().decode())
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        return 0, {}


status = {}
try:
    status = json.loads(Path("/runtime/status.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    pass
business_code, business = get("/business")
healthy = business_code == 200 and bool(business.get("healthy"))
try:
    signal_value = int(status.get("signal_value", 1))
except (TypeError, ValueError):
    signal_value = 1
fault_absent = not bool(status.get("fault_active")) and signal_value == 0
repair_invariant = status.get("rootfs_policy") == "read_only" and (
    status.get("mode") == "baseline" or status.get("repair_mode") == "persistent"
)
persistence = status.get("mode") in {"baseline", "repaired"} and status.get("mechanism")
checks = [
    {"name": "business_operation", "passed": healthy, "weight": 0.35, "detail": f"HTTP {business_code}"},
    {"name": "mechanism_signal_absent", "passed": fault_absent, "weight": 0.30, "detail": str(status)},
    {"name": "repair_invariant", "passed": bool(repair_invariant), "weight": 0.20, "detail": "persistent repair and runtime policy"},
    {"name": "persistence", "passed": bool(persistence), "weight": 0.15, "detail": "repaired state remains represented in live status"},
]
score = sum(float(item["weight"]) for item in checks if item["passed"])
result = {"passed": score >= 1.0, "score": round(score, 6), "checks": checks}
print(json.dumps(result))
raise SystemExit(0 if result["passed"] else 1)
