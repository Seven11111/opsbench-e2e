from __future__ import annotations
import argparse
import json
from pathlib import Path
from common import http_code, scenario
from faults import fault_state

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    case_dir = Path(args.case_dir).resolve()
    implementation = scenario(case_dir).get("implementation", {})
    repaired, details = fault_state(case_dir, implementation, active=False)
    checks = [
        {"name": "business_operation", "passed": details.get("report_template_status") == 200},
        {"name": "fd_stability", "passed": int(details.get("fd_count_after") or 999999) < 25 and int(details.get("fd_growth") or 0) <= 1},
        {"name": "resource_headroom", "passed": int(details.get("fd_count_after") or 999999) < 64},
        {"name": "persistence", "passed": repaired},
    ]
    for item in checks:
        item["weight"] = 1.0 / len(checks)
        item["detail"] = json.dumps(details, ensure_ascii=False, default=str)[:1200]
    passed = all(bool(item["passed"]) for item in checks)
    result = {"passed": passed, "score": round(sum(bool(item["passed"]) for item in checks) / len(checks), 6), "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
