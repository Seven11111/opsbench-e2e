from __future__ import annotations
import argparse
import json
import os
import shlex
import subprocess

QUERY = 'SELECT id, customer_id, payload FROM orders WHERE customer_id = 4242 ORDER BY id LIMIT 50'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = args.case_dir
    compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker compose"))
    compose_file = f"{root}/environment/docker-compose.yaml"
    def psql(sql, json_output=False):
        result = subprocess.run(
            [*compose, "-f", compose_file, "exec", "-T", "db", "psql",
             "-At", "-U", "opsbench", "-d", "app", "-c", sql],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "psql failed")
        value = result.stdout.strip()
        return json.loads(value) if json_output else value
    checks = []
    try:
        row_count = int(psql("SELECT count(*) FROM (" + QUERY + ") q"))
        checks.append({"name": "query_result", "passed": row_count > 0, "weight": 0.2, "detail": f"rows={row_count}"})
        plan = psql("EXPLAIN (ANALYZE, FORMAT JSON) " + QUERY, json_output=True)
        plan_text = json.dumps(plan)
        index_plan = any(token in plan_text for token in ("Index Scan", "Index Only Scan", "Bitmap Index Scan"))
        checks.append({"name": "query_plan", "passed": index_plan and "Seq Scan" not in plan_text, "weight": 0.35, "detail": plan_text[:1200]})
        execution_time = float(plan[0].get("Execution Time", 999999.0)) if isinstance(plan, list) else 999999.0
        checks.append({"name": "query_latency", "passed": execution_time < 1000.0, "weight": 0.25, "detail": f"execution_time_ms={execution_time:.3f}"})
        index_query = """
SELECT COALESCE(string_agg(indexrelid::regclass::text, ',' ORDER BY indexrelid::regclass::text), '')
FROM pg_index i
JOIN pg_class t ON t.oid = i.indrelid
JOIN pg_namespace n ON n.oid = t.relnamespace
JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
WHERE n.nspname = 'public' AND t.relname = 'orders'
  AND a.attname = 'customer_id'
  AND i.indnkeyatts = 1 AND i.indnatts = 1
  AND i.indisvalid AND i.indisready
"""
        index_names = psql(index_query)
        checks.append({"name": "index_presence", "passed": bool(index_names), "weight": 0.1, "detail": index_names})
        ready = subprocess.run(
            [*compose, "-f", compose_file, "exec", "-T", "db", "pg_isready", "-U", "opsbench", "-d", "app"],
            capture_output=True, text=True, check=False,
        )
        checks.append({"name": "service_health", "passed": ready.returncode == 0, "weight": 0.1, "detail": ready.stdout.strip()})
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        checks.append({"name": "verifier_execution", "passed": False, "weight": 1.0, "detail": str(exc)})
    score = sum(item["weight"] for item in checks if item["passed"])
    result = {"passed": score >= 1.0, "score": round(score, 6), "checks": checks}
    print(json.dumps(result))
    return 0 if result["passed"] else 1
if __name__ == "__main__":
    raise SystemExit(main())
