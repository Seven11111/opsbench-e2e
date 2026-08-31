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
    budget_ms = float(details.get("request_latency_budget_ms") or 0)
    checks = [
        {"name": "business_operation", "passed": details.get("orders_status") == 200},
        # The budget is a public contract value returned by slo_read and
        # recorded in manifest.public_actionability.thresholds.  Do not hide a
        # second delay threshold in the verifier.
        {"name": "request_latency_slo", "passed": budget_ms > 0 and float(details.get("upstream_elapsed_ms") or 999999) < budget_ms},
        {"name": "timeout_policy", "passed": budget_ms > 0 and bool(details.get("timeout_covers_delay")) and int(details.get("client_timeout_ms") or 0) <= budget_ms},
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
