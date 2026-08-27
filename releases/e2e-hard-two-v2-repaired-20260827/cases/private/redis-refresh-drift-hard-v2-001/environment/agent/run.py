from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

RUNTIME = Path("/runtime")


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(command: list[str], timeout: int = 10) -> dict:
    started = time.monotonic()
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
        return {
            "returncode": completed.returncode,
            "stdout": (completed.stdout or "")[-10000:],
            "stderr": (completed.stderr or "")[-2000:],
            "duration_sec": round(time.monotonic() - started, 4),
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {"returncode": 124, "stdout": "", "stderr": str(exc), "duration_sec": round(time.monotonic() - started, 4)}


def http_get(url: str) -> tuple[int, str, float]:
    started = time.monotonic()
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url, timeout=5) as response:
            return int(response.status), response.read(4000).decode("utf-8", errors="replace"), time.monotonic() - started
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read(4000).decode("utf-8", errors="replace"), time.monotonic() - started
    except Exception as exc:
        return 0, str(exc), time.monotonic() - started


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip().lower()] = value.strip()
    return values


def write_env(path: Path, values: dict[str, str]) -> None:
    path.write_text("".join(f"{key}={value}\n" for key, value in sorted(values.items())), encoding="utf-8")


def build_tools(trace_dir: Path, public_names: list[str]):
    mode = os.environ.get("OPSBENCH_CASE_MODE", "")

    def record(name: str, inputs: dict, result: Any) -> str:
        append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": name, "input": inputs, "result": result})
        return json.dumps(result, ensure_ascii=False)

    @tool
    def business_probe(endpoint: str, repeat: int = 1) -> str:
        """Probe a declared business endpoint and return bounded status and latency observations."""
        ports = {"postgres-recurring-lock-v2": 18085, "redis-refresh-drift-v2": 18087}
        allowed = {
            "postgres-recurring-lock-v2": {"orders", "reports", "inventory-sync"},
            "redis-refresh-drift-v2": {"catalog", "catalog-preview"},
        }
        if endpoint not in allowed.get(mode, set()):
            return record("business_probe", {"endpoint": endpoint, "repeat": repeat}, {"error": "endpoint is not declared"})
        observations = []
        for _ in range(max(1, min(int(repeat), 5))):
            status, body, duration = http_get(f"http://127.0.0.1:{ports[mode]}/{endpoint}")
            observations.append({"http_status": status, "body": body[-1000:], "duration_sec": round(duration, 4)})
            time.sleep(0.2)
        return record("business_probe", {"endpoint": endpoint, "repeat": repeat}, {"observations": observations})

    @tool
    def service_status(service: str) -> str:
        """Read bounded process or health status for one declared service."""
        result: dict[str, Any]
        if mode == "postgres-recurring-lock-v2":
            if service == "postgres":
                result = run(["pg_isready", "-h", "db", "-U", "opsbench", "-d", "app"])
            elif service == "orders-api":
                status, body, duration = http_get("http://127.0.0.1:18085/health")
                result = {"http_status": status, "body": body, "duration_sec": round(duration, 4)}
            elif service == "inventory-sync":
                pid_path = RUNTIME / "inventory-worker.pid"
                pid = pid_path.read_text(encoding="utf-8").strip() if pid_path.exists() else ""
                last = (RUNTIME / "last-sync.json").read_text(encoding="utf-8") if (RUNTIME / "last-sync.json").exists() else ""
                result = {"worker_pid": pid, "supervised": True, "last_completed_cycle": last}
            else:
                result = {"error": "service is not declared"}
        else:
            if service == "redis":
                result = run(["redis-cli", "-h", "redis", "PING"])
            elif service == "catalog-api":
                status, body, duration = http_get("http://127.0.0.1:18087/health")
                result = {"http_status": status, "body": body, "duration_sec": round(duration, 4)}
            elif service == "cache-refresh":
                pid_path = RUNTIME / "refresh-worker.pid"
                pid = pid_path.read_text(encoding="utf-8").strip() if pid_path.exists() else ""
                last = (RUNTIME / "last-refresh.json").read_text(encoding="utf-8") if (RUNTIME / "last-refresh.json").exists() else ""
                result = {"worker_pid": pid, "supervised": True, "last_completed_refresh": last}
            else:
                result = {"error": "service is not declared"}
        return record("service_status", {"service": service}, result)

    @tool
    def query_logs(service: str, contains: str = "", limit: int = 50) -> str:
        """Read a bounded service log window without returning a diagnosis or repair recommendation."""
        log_map = {
            "orders-api": RUNTIME / "orders.log",
            "inventory-sync": RUNTIME / "inventory-worker.log",
            "catalog-api": RUNTIME / "catalog.log",
            "cache-refresh": RUNTIME / "refresh-worker.log",
        }
        path = log_map.get(service)
        if not path or not path.exists():
            return record("query_logs", {"service": service, "contains": contains, "limit": limit}, {"error": "log is not declared"})
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if contains:
            lines = [line for line in lines if contains.casefold() in line.casefold()]
        result = {"lines": lines[-max(1, min(int(limit), 100)):]}
        return record("query_logs", {"service": service, "contains": contains, "limit": limit}, result)

    @tool
    def query_postgres(view: str, application_name: str = "", pid: int = 0) -> str:
        """Read one allowlisted PostgreSQL observability view."""
        if mode != "postgres-recurring-lock-v2":
            return record("query_postgres", {"view": view}, {"error": "tool is not declared for this case"})
        queries = {
            "activity": "SELECT pid,application_name,state,coalesce(wait_event_type,''),coalesce(wait_event,''),left(query,120) FROM pg_stat_activity WHERE datname='app' ORDER BY pid;",
            "locks": "SELECT a.pid,a.application_name,l.locktype,coalesce(l.objid::text,''),l.granted FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid WHERE a.datname='app' ORDER BY a.pid,l.locktype;",
            "blocking_graph": "SELECT pid,application_name,pg_blocking_pids(pid),coalesce(wait_event_type,''),coalesce(wait_event,'') FROM pg_stat_activity WHERE datname='app' ORDER BY pid;",
            "database_stats": "SELECT datname,numbackends,xact_commit,xact_rollback FROM pg_stat_database WHERE datname='app';",
        }
        if view not in queries:
            return record("query_postgres", {"view": view}, {"error": "view is not allowlisted"})
        result = run(["psql", "-h", "db", "-U", "opsbench", "-d", "app", "-At", "-F", "|", "-c", queries[view]])
        if application_name:
            result["stdout"] = "\n".join(line for line in result.get("stdout", "").splitlines() if application_name.casefold() in line.casefold())
        if pid:
            result["stdout"] = "\n".join(line for line in result.get("stdout", "").splitlines() if line.split("|", 1)[0] == str(pid))
        return record("query_postgres", {"view": view, "application_name": application_name, "pid": pid}, result)

    @tool
    def read_service_config(service: str, layer: str, key: str) -> str:
        """Read one allowlisted base, environment, or effective configuration value."""
        if mode == "postgres-recurring-lock-v2":
            if service != "inventory-sync" or key not in {"lock_mode", "lock_key", "transaction_scope", "schedule_enabled"}:
                result = {"error": "configuration key is not declared"}
            else:
                base = json.loads((RUNTIME / "base_config.json").read_text(encoding="utf-8"))
                env = read_env(RUNTIME / "inventory.env")
                values = base if layer == "base" else env if layer == "environment" else {**base, **env} if layer == "effective" else {}
                result = {"service": service, "layer": layer, "key": key, "present": key in values, "value": values.get(key)}
        else:
            if service not in {"catalog-api", "cache-refresh"} or key not in {"schema_version", "refresh_interval_sec", "ttl_sec", "validation_enabled"}:
                result = {"error": "configuration key is not declared"}
            else:
                base = json.loads((RUNTIME / ("refresh-base.json" if service == "cache-refresh" else "catalog-base.json")).read_text(encoding="utf-8"))
                env = read_env(RUNTIME / "refresh.env") if service == "cache-refresh" else {}
                values = base if layer == "base" else env if layer == "environment" else {**base, **env} if layer == "effective" else {}
                result = {"service": service, "layer": layer, "key": key, "present": key in values, "value": values.get(key)}
        return record("read_service_config", {"service": service, "layer": layer, "key": key}, result)

    @tool
    def update_service_config(service: str, layer: str, key: str, operation: str, value: str = "") -> str:
        """Set or remove one allowlisted environment override using explicit parameters."""
        if layer != "environment" or operation not in {"set", "remove"}:
            result = {"error": "only set/remove on the environment layer is supported"}
        elif mode == "postgres-recurring-lock-v2" and service == "inventory-sync" and key in {"lock_mode", "transaction_scope"}:
            path = RUNTIME / "inventory.env"; values = read_env(path)
            if operation == "remove": values.pop(key, None)
            else: values[key] = value
            write_env(path, values); result = {"updated": True, "service": service, "key": key, "operation": operation}
        elif mode == "redis-refresh-drift-v2" and service == "cache-refresh" and key in {"schema_version", "ttl_sec"}:
            path = RUNTIME / "refresh.env"; values = read_env(path)
            if operation == "remove": values.pop(key, None)
            else: values[key] = value
            write_env(path, values); result = {"updated": True, "service": service, "key": key, "operation": operation}
        else:
            result = {"error": "configuration change is not declared"}
        append_jsonl(RUNTIME / "audit.jsonl", {"event": "config_update", "service": service, "key": key, "operation": operation, "value": value, "time": time.time()})
        return record("update_service_config", {"service": service, "layer": layer, "key": key, "operation": operation, "value": value}, result)

    @tool
    def terminate_postgres_backend(pid: int) -> str:
        """Terminate exactly one PostgreSQL backend by PID."""
        if mode != "postgres-recurring-lock-v2" or int(pid) < 2:
            result = {"error": "backend target is not valid"}
        else:
            result = run(["psql", "-h", "db", "-U", "opsbench", "-d", "app", "-At", "-c", f"SELECT pg_terminate_backend({int(pid)});"])
        append_jsonl(RUNTIME / "audit.jsonl", {"event": "terminate_backend", "pid": int(pid), "time": time.time()})
        return record("terminate_postgres_backend", {"pid": pid}, result)

    @tool
    def redis_inspect(key: str, field: str) -> str:
        """Read bounded metadata or value information for one allowlisted Redis key."""
        if mode != "redis-refresh-drift-v2" or key not in {"catalog:active", "catalog:meta", "catalog:preview"} or field not in {"value", "type", "ttl", "memory"}:
            result = {"error": "key or field is not declared"}
        else:
            command = {"value": "GET", "type": "TYPE", "ttl": "TTL", "memory": "MEMORY USAGE"}[field].split()
            result = run(["redis-cli", "-h", "redis", "--raw", *command, key])
        return record("redis_inspect", {"key": key, "field": field}, result)

    @tool
    def run_cache_refresh(mode: str) -> str:
        """Trigger one normal cache refresh using the current effective configuration."""
        if os.environ.get("OPSBENCH_CASE_MODE") != "redis-refresh-drift-v2" or mode != "normal":
            result = {"error": "refresh mode is not declared"}
        else:
            trigger = RUNTIME / "refresh.trigger"
            trigger.write_text(str(time.time()), encoding="utf-8")
            before = trigger.stat().st_mtime
            deadline = time.time() + 8
            while time.time() < deadline:
                last = RUNTIME / "last-refresh.json"
                if last.exists() and last.stat().st_mtime >= before:
                    break
                time.sleep(0.2)
            result = {"triggered": True, "last_refresh": (RUNTIME / "last-refresh.json").read_text(encoding="utf-8") if (RUNTIME / "last-refresh.json").exists() else ""}
        return record("run_cache_refresh", {"mode": mode}, result)

    @tool
    def restart_service(service: str) -> str:
        """Restart one declared worker service; its supervisor will recreate it."""
        if mode == "postgres-recurring-lock-v2" and service == "inventory-sync":
            pid_path = RUNTIME / "inventory-worker.pid"
            try: os.kill(int(pid_path.read_text(encoding="utf-8")), 15)
            except (OSError, ValueError): pass
            pid_path.unlink(missing_ok=True)
            result = {"restart_requested": True, "service": service}
        elif mode == "redis-refresh-drift-v2" and service == "cache-refresh":
            pid_path = RUNTIME / "refresh-worker.pid"
            try: os.kill(int(pid_path.read_text(encoding="utf-8")), 15)
            except (OSError, ValueError): pass
            pid_path.unlink(missing_ok=True)
            result = {"restart_requested": True, "service": service}
        else:
            result = {"error": "service is not declared for restart"}
        append_jsonl(RUNTIME / "audit.jsonl", {"event": "service_restart", "service": service, "time": time.time()})
        return record("restart_service", {"service": service}, result)

    all_tools = {
        item.name: item for item in [business_probe, service_status, query_logs, query_postgres,
                                     read_service_config, update_service_config,
                                     terminate_postgres_backend, redis_inspect,
                                     run_cache_refresh, restart_service]
    }
    return [all_tools[name] for name in public_names if name in all_tools]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task")
    parser.add_argument("--tools")
    parser.add_argument("--trace")
    parser.add_argument("--case-dir")
    parser.add_argument("--work-dir")
    parser.add_argument("--timeout-sec", type=int, default=300)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    task_path = Path(args.task or os.environ.get("OPSBENCH_TASK", "/opsbench/public/task.md"))
    tools_path = Path(args.tools or os.environ.get("OPSBENCH_TOOLS", "/opsbench/public/tools.json"))
    trace_dir = Path(args.trace or os.environ.get("OPSBENCH_TRACE", "/opsbench/trace"))
    trace_dir.mkdir(parents=True, exist_ok=True)
    task = task_path.read_text(encoding="utf-8")
    tool_contract = json.loads(tools_path.read_text(encoding="utf-8"))
    public_names = [item["name"] for item in tool_contract.get("tools", [])]
    model_name = os.environ.get("OPSBENCH_AGENT_MODEL") or os.environ.get("OPSBENCH_MODEL") or "deepseek-v4-flash"
    write_json(trace_dir / "agent_start.json", {"protocol_id":"opsbench-agent-v1","tool_names":public_names,"model":model_name})
    api_key = os.environ.get("OPSBENCH_API_KEY")
    if not api_key:
        write_json(trace_dir / "agent_result.json", {"passed":False,"error":"OPSBENCH_API_KEY is missing"}); return 2
    model = ChatOpenAI(model=model_name, api_key=api_key,
                       base_url=os.environ.get("OPSBENCH_BASE_URL", "https://api.deepseek.com"),
                       temperature=0, timeout=int(os.environ.get("OPSBENCH_REQUEST_TIMEOUT", "45")),
                       max_retries=int(os.environ.get("OPSBENCH_MAX_RETRIES", "2")))
    os.environ.pop("OPSBENCH_API_KEY", None)
    tool_contract_text = json.dumps(tool_contract, ensure_ascii=False, indent=2)
    prompt = f"""You are an operations repair agent in a reproducible sandbox. Investigate actively: start from public symptoms, choose bounded observations, form and test hypotheses, then apply the smallest safe change. Tool outputs are observations, not diagnoses. A visible bad state may be recreated by an upstream process, so distinguish immediate effects from durable causes. Do not guess PIDs or configuration values. Preserve unrelated work and verify recovery across the lifecycle requested by the task. Never search for hidden files, verifier code, case roots, credentials, or Docker sockets.

Use only the exact public tool contract below. The enum values are authoritative: do not invent service names, endpoint names, key names, or fields. If a tool returns an allowlist error, stop guessing and choose a value from this contract.
PUBLIC TOOL CONTRACT:
{tool_contract_text}

For this task, inspect the declared catalog endpoints, Redis keys, refresh logs, and effective cache-refresh configuration before changing anything. Compare the base and effective schema_version. If the live fault is an environment override, remove that declared override with update_service_config rather than overwriting the Redis key. Then trigger or restart only the declared refresh worker and verify across another refresh cycle. Do not delete the active key, disable validation, or change TTL."""
    agent = create_react_agent(model, build_tools(trace_dir, public_names), prompt=prompt)
    try:
        result = agent.invoke({"messages":[("user", task)]}, config={"recursion_limit":max(1, int(os.environ.get("OPSBENCH_AGENT_MAX_STEPS", "60")))})
        messages = result.get("messages", [])
        for index, message in enumerate(messages):
            append_jsonl(trace_dir / "agent_messages.jsonl", {"index":index,"type":type(message).__name__,"content":str(getattr(message,"content","")),"tool_calls":getattr(message,"tool_calls",None) or []})
        write_json(trace_dir / "agent_result.json", {"passed":True,"message_count":len(messages),"final":str(messages[-1].content) if messages else ""}); return 0
    except Exception as exc:
        write_json(trace_dir / "agent_result.json", {"passed":False,"error":str(exc)}); return 1


if __name__ == "__main__":
    raise SystemExit(main())
