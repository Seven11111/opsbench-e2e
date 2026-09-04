"""Small OpsBench-compatible LangChain ReAct agent.

The agent is intended to run inside the E2E target container.  It only gets
the public task, public tool description, and a writable trace directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


_BLOCKED_SHELL_TOKENS = (
    "service.py",
    "init.sql",
    "dockerfile",
    "/evaluator",
    "scenario.json",
    "manifest.yaml",
    "docker.sock",
    "/var/run/docker",
    "/opt/opsbench",
    "/case-root",
    "case-dir",
    "docker inspect",
    "/proc/",
    "opsbench_api_key",
)


def _blocked_shell_command(command: str) -> str | None:
    """Reject obvious attempts to inspect hidden case implementation data."""
    normalized = re.sub(r"\s+", " ", str(command).strip().lower())
    for token in _BLOCKED_SHELL_TOKENS:
        if token in normalized:
            return f"shell command blocked by opsbench-agent policy: {token}"
    if re.fullmatch(r"(?:env|printenv|set|export)(?:\s+.*)?", normalized):
        return "shell command blocked by opsbench-agent policy: environment inspection"
    return None


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def build_tools(trace_dir: Path):
    @tool
    def shell(command: str) -> str:
        """Run a diagnostic or repair shell command inside the target container."""
        started = time.monotonic()
        blocked = _blocked_shell_command(command)
        if blocked:
            result = {
                "returncode": 126,
                "stdout": "",
                "stderr": blocked,
                "duration_sec": round(time.monotonic() - started, 4),
            }
            _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "shell", "input": command, "result": result})
            return json.dumps(result, ensure_ascii=False)
        try:
            child_env = {
                key: value
                for key, value in os.environ.items()
                if key not in {"OPSBENCH_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"}
            }
            completed = subprocess.run(
                ["/bin/sh", "-lc", command],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                env=child_env,
            )
            result = {
                "returncode": completed.returncode,
                "stdout": (completed.stdout or "")[-12000:],
                "stderr": (completed.stderr or "")[-12000:],
                "duration_sec": round(time.monotonic() - started, 4),
            }
        except subprocess.TimeoutExpired:
            result = {
                "returncode": 124,
                "stdout": "",
                "stderr": "command timed out after 30 seconds",
                "duration_sec": round(time.monotonic() - started, 4),
            }
        _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "shell", "input": command, "result": result})
        return json.dumps(result, ensure_ascii=False)

    @tool
    def health_check() -> str:
        """Read the live service health signal after a repair."""
        started = time.monotonic()
        health_mode = os.environ.get("OPSBENCH_HEALTH_MODE", "status")
        if health_mode == "postgres":
            try:
                completed = subprocess.run(
                    ["pg_isready", "-h", os.environ.get("PGHOST", "db"),
                     "-U", os.environ.get("PGUSER", "opsbench"),
                     "-d", os.environ.get("PGDATABASE", "app")],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                    env={key: value for key, value in os.environ.items()
                         if key not in {"OPSBENCH_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"}},
                )
                result = {
                    "healthy": completed.returncode == 0,
                    "status": {"stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]},
                    "duration_sec": round(time.monotonic() - started, 4),
                }
                _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "health_check", "input": {}, "result": result})
                return json.dumps(result, ensure_ascii=False)
            except (OSError, subprocess.SubprocessError) as exc:
                result = {"healthy": False, "status": {"error": str(exc)}, "duration_sec": round(time.monotonic() - started, 4)}
                _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "health_check", "input": {}, "result": result})
                return json.dumps(result, ensure_ascii=False)
        status_path = Path("/runtime/status.json")
        status: dict[str, Any] = {}
        if status_path.exists():
            try:
                status = json.loads(status_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                status = {"healthy": False, "error": "invalid status.json"}
        result = {
            "healthy": bool(status.get("healthy", False)),
            "status": status,
            "duration_sec": round(time.monotonic() - started, 4),
        }
        _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "health_check", "input": {}, "result": result})
        return json.dumps(result, ensure_ascii=False)

    return [shell, health_check]


def _invoke_public_tool(tool_map: dict[str, Any], name: str, payload: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
    item = tool_map.get(name)
    if item is None:
        result = {"ok": False, "error": f"public tool {name!r} is unavailable"}
    else:
        try:
            raw = item.invoke(payload)
            if isinstance(raw, dict):
                result = raw
            else:
                try:
                    result = json.loads(str(raw))
                except json.JSONDecodeError:
                    result = {"ok": True, "raw": str(raw)}
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
    steps.append({"tool": name, "input": payload, "result": result})
    return result


def run_public_oracle(public_tools: dict[str, Any], trace_dir: Path) -> int:
    """Kill only the observed listener blocker, then verify live HTTP health."""
    declared = {
        str(item.get("name") or "")
        for item in public_tools.get("tools", [])
        if isinstance(item, dict)
    }
    trace: list[dict[str, Any]] = []
    tool_map = {str(item.name): item for item in build_tools(trace_dir)}
    if not {"shell", "health_check"}.issubset(declared):
        result = {"passed": False, "error": "public tools do not expose shell and health_check", "steps": trace}
        _write_json(trace_dir / "agent_result.json", result)
        return 1
    repair = _invoke_public_tool(
        tool_map,
        "shell",
        {"command": "pid=$(pgrep -f 'port_blocker.py' | head -n 1); if [ -n \"$pid\" ]; then kill \"$pid\"; fi"},
        trace,
    )
    time.sleep(1.5)
    health = _invoke_public_tool(tool_map, "health_check", {}, trace)
    passed = int(repair.get("returncode", 1)) == 0 and bool(health.get("healthy"))
    result = {"passed": passed, "mode": "public_tool_oracle", "steps": trace}
    _write_json(trace_dir / "agent_result.json", result)
    return 0 if passed else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task")
    parser.add_argument("--tools")
    parser.add_argument("--trace")
    parser.add_argument("--case-dir")
    parser.add_argument("--work-dir")
    parser.add_argument("--timeout-sec", type=int, default=300)
    parser.add_argument("--public-oracle", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    task_path = Path(args.task or os.environ.get("OPSBENCH_TASK", "/opsbench/public/task.md"))
    tools_path = Path(args.tools or os.environ.get("OPSBENCH_TOOLS", "/opsbench/public/tools.json"))
    trace_dir = Path(args.trace or os.environ.get("OPSBENCH_TRACE", "/opsbench/trace"))
    trace_dir.mkdir(parents=True, exist_ok=True)

    task = task_path.read_text(encoding="utf-8")
    public_tools = json.loads(tools_path.read_text(encoding="utf-8"))
    _write_json(trace_dir / "agent_start.json", {
        "protocol_id": "opsbench-agent-v1",
        "task_path": str(task_path),
        "tools_path": str(tools_path),
        "tool_names": [item.get("name") for item in public_tools.get("tools", [])],
        "model": os.environ.get("OPSBENCH_AGENT_MODEL") or os.environ.get("OPSBENCH_MODEL") or "deepseek-v4-flash",
    })

    if args.public_oracle:
        return run_public_oracle(public_tools, trace_dir)

    api_key = os.environ.get("OPSBENCH_API_KEY")
    base_url = os.environ.get("OPSBENCH_BASE_URL", "https://api.deepseek.com")
    model_name = os.environ.get("OPSBENCH_AGENT_MODEL") or os.environ.get("OPSBENCH_MODEL") or "deepseek-v4-flash"
    if not api_key:
        _write_json(trace_dir / "agent_result.json", {"passed": False, "error": "OPSBENCH_API_KEY is missing"})
        return 2

    system_prompt = """You are an operations repair agent running inside the target container.
Use the public task and tools to diagnose the live service, make the smallest safe
repair, and verify the result. Start with health_check, then use shell only for
commands relevant to the stated operational objective. Do not edit service code,
start replacement sidecars, or kill or replace PID 1. Only operate under the
runtime directory and the public files under /opsbench. Do not look for verifier,
scenario, hidden labels, case-root files, Docker sockets, host files, or host
credentials. Finish only after the public health signal is healthy."""
    model = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
        timeout=int(os.environ.get("OPSBENCH_REQUEST_TIMEOUT", "300")),
        max_retries=int(os.environ.get("OPSBENCH_MAX_RETRIES", "2")),
    )
    agent = create_react_agent(model, build_tools(trace_dir), prompt=system_prompt)
    try:
        result = agent.invoke(
            {"messages": [("user", task)]},
            config={"recursion_limit": 40},
        )
        messages = result.get("messages", [])
        final_text = messages[-1].content if messages else ""
        _write_json(trace_dir / "agent_result.json", {
            "passed": True,
            "message_count": len(messages),
            "final": final_text,
        })
        return 0
    except Exception as exc:
        _write_json(trace_dir / "agent_result.json", {"passed": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
