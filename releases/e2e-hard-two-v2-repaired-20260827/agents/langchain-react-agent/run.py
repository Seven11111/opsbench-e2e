"""Small OpsBench-compatible LangChain ReAct agent.

The agent is intended to run inside the E2E target container.  It only gets
the public task, public tool description, and a writable trace directory.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
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
    "find /",
    "grep -r /",
    "grep -rl /",
    "ls -lar /",
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


def _post_retry(url: str, *, body: bytes = b"", attempts: int = 3) -> bool:
    """POST to a case-declared internal control endpoint without proxies."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for attempt in range(max(1, attempts)):
        request = urllib.request.Request(url, method="POST", data=body)
        request.add_header("Content-Type", "application/json")
        try:
            with opener.open(request, timeout=8) as response:
                response.read(4000)
                if int(response.status) == 200:
                    return True
        except (OSError, urllib.error.URLError):
            if attempt + 1 < attempts:
                time.sleep(0.5)
    return False


def build_tools(trace_dir: Path):
    command_history: dict[str, int] = {}

    def _rabbitmq_get(path: str) -> tuple[int, str]:
        """Read a bounded RabbitMQ management API endpoint.

        RabbitMQ runs as a separate service from the Python Agent runner.  The
        agent therefore uses the public, case-declared management endpoint
        instead of assuming that broker CLI binaries are installed in the
        runner image.
        """
        base_url = os.environ.get("OPSBENCH_RABBITMQ_URL", "http://rabbitmq:15672").rstrip("/")
        user = os.environ.get("OPSBENCH_RABBITMQ_USER", "opsbench")
        password = os.environ.get("OPSBENCH_RABBITMQ_PASS", "opsbench-local-only")
        request = urllib.request.Request(f"{base_url}{path}")
        token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
        request.add_header("Authorization", f"Basic {token}")
        with urllib.request.urlopen(request, timeout=8) as response:
            return int(response.status), response.read(12000).decode("utf-8", errors="replace")

    @tool
    def shell(command: str) -> str:
        """Run a diagnostic or repair shell command inside the target container."""
        started = time.monotonic()
        normalized_command = re.sub(r"\s+", " ", str(command).strip())
        command_key = normalized_command.casefold()
        command_history[command_key] = command_history.get(command_key, 0) + 1
        if command_history[command_key] > 2:
            result = {
                "returncode": 125,
                "stdout": "",
                "stderr": "shell command blocked by opsbench-agent policy: repeated command",
                "duration_sec": round(time.monotonic() - started, 4),
            }
            _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "shell", "input": command, "result": result})
            return json.dumps(result, ensure_ascii=False)
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
                timeout=10,
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
                "stderr": "command timed out after 10 seconds",
                "duration_sec": round(time.monotonic() - started, 4),
            }
        _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "shell", "input": command, "result": result})
        return json.dumps(result, ensure_ascii=False)

    @tool
    def business_check() -> str:
        """Check the public business operation, not just process liveness."""
        started = time.monotonic()
        url = os.environ.get("OPSBENCH_BUSINESS_CHECK_URL", "").strip()
        if not url:
            result = {
                "healthy": False,
                "status": {"error": "business check is not configured for this case"},
                "duration_sec": round(time.monotonic() - started, 4),
            }
            _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "business_check", "input": {}, "result": result})
            return json.dumps(result, ensure_ascii=False)
        curl_args = [
            "curl", "-sS", "--noproxy", "*", "--max-time", "5",
            "-o", "/tmp/opsbench-business-check", "-w", "%{http_code}", url,
        ]
        cacert = os.environ.get("OPSBENCH_BUSINESS_CHECK_CACERT", "").strip()
        resolve = os.environ.get("OPSBENCH_BUSINESS_CHECK_RESOLVE", "").strip()
        if cacert:
            curl_args[1:1] = ["--cacert", cacert]
        if resolve:
            curl_args[1:1] = ["--resolve", resolve]
        try:
            completed = subprocess.run(curl_args, capture_output=True, text=True, timeout=8, check=False)
            status_text = (completed.stdout or "").strip()
            status_code = int(status_text[-3:]) if status_text[-3:].isdigit() else 0
            result = {
                "healthy": status_code == 200,
                "status": {
                    "http_status": status_code,
                    "url": url,
                    "stderr": (completed.stderr or "")[-2000:],
                },
                "duration_sec": round(time.monotonic() - started, 4),
            }
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            result = {
                "healthy": False,
                "status": {"url": url, "error": str(exc)},
                "duration_sec": round(time.monotonic() - started, 4),
            }
        _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "business_check", "input": {}, "result": result})
        return json.dumps(result, ensure_ascii=False)

    @tool
    def metrics_query(metric: str = "") -> str:
        """Read one bounded, case-declared live metrics endpoint."""
        started = time.monotonic()
        url = os.environ.get("OPSBENCH_METRICS_URL", "").strip()
        if not url:
            result = {"healthy": False, "status": {"error": "metrics endpoint is not configured"}, "duration_sec": round(time.monotonic() - started, 4)}
        else:
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    body = response.read(8000).decode("utf-8", errors="replace")
                result = {"healthy": True, "status": {"metric": metric, "body": body}, "duration_sec": round(time.monotonic() - started, 4)}
            except (OSError, urllib.error.URLError) as exc:
                result = {"healthy": False, "status": {"metric": metric, "error": str(exc)}, "duration_sec": round(time.monotonic() - started, 4)}
        _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "metrics_query", "input": {"metric": metric}, "result": result})
        return json.dumps(result, ensure_ascii=False)

    @tool
    def message_probe() -> str:
        """Inspect the declared RabbitMQ alarm and queue-flow signals."""
        started = time.monotonic()
        try:
            alarm_status, alarm_body = _rabbitmq_get("/api/health/checks/alarms")
            queue_status, queue_body = _rabbitmq_get("/api/queues/%2F")
            result = {
                "healthy": alarm_status == 200 and queue_status == 200,
                "status": {
                    "alarm_http_status": alarm_status,
                    "alarms": alarm_body[-4000:],
                    "queue_http_status": queue_status,
                    "queues": queue_body[-4000:],
                },
                "duration_sec": round(time.monotonic() - started, 4),
            }
        except (OSError, urllib.error.URLError, subprocess.SubprocessError) as exc:
            result = {
                "healthy": False,
                "status": {"error": str(exc)},
                "duration_sec": round(time.monotonic() - started, 4),
            }
        _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "message_probe", "input": {}, "result": result})
        return json.dumps(result, ensure_ascii=False)

    @tool
    def service_repair(stage: str = "", action: str = "") -> str:
        """Apply the registered repair in the declared prepare/apply stages."""
        started = time.monotonic()
        mode = os.environ.get("OPSBENCH_SERVICE_REPAIR_MODE", "")
        stage = str(stage or "").strip().lower()
        action = str(action or "").strip().lower()
        result: dict[str, Any]
        second_batch_modes = {
            "postgres_lock_contention_v1",
            "postgres_connection_pool_exhaustion_v1",
            "redis_cache_corruption_v1",
            "kafka_consumer_lag_v1",
            "http_retry_circuit_breaker_v1",
        }
        hard_modes = {
            "http_dependency_port_drift_v1",
            "http_dependency_dns_poison_v1",
            "http_dependency_timeout_slo_v1",
            "app_config_precedence_v1",
            "linux_fd_leak_v1",
            "tls_hostname_mismatch_v1",
        }
        expected_actions = {
            "postgres_lock_contention_v1": ("terminate_lock_holders", "terminate_lock_holders"),
            "postgres_connection_pool_exhaustion_v1": ("release_pool_holders", "release_pool_holders"),
            "redis_cache_corruption_v1": ("rebuild_cache_payload", "rebuild_cache_payload"),
            "kafka_consumer_lag_v1": ("pause_producer", "resume_consumer"),
            "http_retry_circuit_breaker_v1": ("recover_dependency", "recover_dependency"),
            "http_dependency_port_drift_v1": ("restore_dependency_port", "restore_dependency_port"),
            "http_dependency_dns_poison_v1": ("restore_dns_mapping", "restore_dns_mapping"),
            "http_dependency_timeout_slo_v1": ("restore_dependency_slo", "restore_dependency_slo"),
            "app_config_precedence_v1": ("remove_environment_override", "remove_environment_override"),
            "linux_fd_leak_v1": ("disable_template_fd_leak", "disable_template_fd_leak"),
            "tls_hostname_mismatch_v1": ("restore_certificate_identity", "restore_certificate_identity"),
        }
        try:
            if mode == "fluentbit_backpressure_v1":
                path = Path("/runtime/fluent-bit.conf")
                path.write_text(path.read_text(encoding="utf-8").replace("Host         missing-sink", "Host         sink"), encoding="utf-8")
                result = {"healthy": _post_retry("http://fluent-bit:2020/api/v2/reload", body=b"{}"), "action": "restore_output_and_reload"}
            elif mode == "prometheus_scrape_target_v1":
                path = Path("/runtime/prometheus.yml")
                path.write_text(path.read_text(encoding="utf-8").replace("missing-exporter:19999", "exporter:19100"), encoding="utf-8")
                result = {"healthy": _post_retry("http://prometheus:9090/-/reload"), "action": "restore_scrape_target_and_reload"}
            elif mode in second_batch_modes or mode in hard_modes:
                state_path = (
                    trace_dir / "agent_repair_state.json"
                    if mode in hard_modes
                    else Path("/runtime/state.json")
                )
                # Persist the staged-repair handshake in the trace mount.  The
                # hard cases intentionally do not expose a writable /runtime
                # path to the agent; using the authorized trace directory
                # keeps the prepare/apply protocol functional without adding
                # a hidden case or host path.
                diagnosis_path = trace_dir / "agent_diagnosis.json"
                state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
                expected_action = expected_actions[mode][0] if stage == "prepare" else expected_actions[mode][1] if stage == "apply" else ""
                if stage not in {"prepare", "apply"}:
                    result = {"healthy": False, "error": "stage is required: call prepare, then apply"}
                elif action != expected_action:
                    result = {
                        "healthy": False,
                        "error": "repair action does not match the diagnosed failure or repair stage",
                    }
                elif not diagnosis_path.exists():
                    result = {"healthy": False, "error": "diagnose must be called before service_repair"}
                elif stage == "prepare":
                    state["repair_stage"] = "prepared"
                    if mode == "kafka_consumer_lag_v1":
                        state["producer_paused"] = True
                    state_path.write_text(json.dumps(state), encoding="utf-8")
                    result = {"healthy": True, "action": "repair_prepared", "next_stage": "apply"}
                elif state.get("repair_stage") != "prepared":
                    result = {"healthy": False, "error": "repair stage order violation: prepare is required first"}
                else:
                    command_result = None
                    if mode == "postgres_lock_contention_v1":
                        command_result = subprocess.run(
                            ["sh", "-lc", "PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE application_name='opsbench-lock-holder';\""],
                            capture_output=True, text=True, timeout=10, check=False,
                        )
                    elif mode == "postgres_connection_pool_exhaustion_v1":
                        command_result = subprocess.run(
                            ["sh", "-lc", "PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE application_name='opsbench-pool-holder';\""],
                            capture_output=True, text=True, timeout=10, check=False,
                        )
                    elif mode == "redis_cache_corruption_v1":
                        command_result = subprocess.run(
                            ["redis-cli", "-h", "redis", "SET", "catalog:v1", '{"version":1,"items":["a"]}'],
                            capture_output=True, text=True, timeout=10, check=False,
                        )
                    elif mode == "app_config_precedence_v1":
                        command_result = subprocess.run(
                            ["sh", "-lc", "rm -f /etc/opsbench/app.env && /opt/opsbench/runtime/appctl.sh restart"],
                            capture_output=True, text=True, timeout=20, check=False,
                        )
                    elif mode == "http_dependency_port_drift_v1":
                        command_result = subprocess.run(
                            ["sh", "-lc", "rm -f /etc/opsbench/dependency.env && /opt/opsbench/runtime/dependencyctl.sh restart"],
                            capture_output=True, text=True, timeout=20, check=False,
                        )
                    elif mode == "http_dependency_dns_poison_v1":
                        command_result = subprocess.run(
                            ["sh", "-lc", "sed '/[[:space:]]catalog\\.internal$/d' /etc/hosts >/tmp/opsbench-hosts && cat /tmp/opsbench-hosts >/etc/hosts && printf '%s\\n' '127.0.0.1 catalog.internal' >>/etc/hosts"],
                            capture_output=True, text=True, timeout=20, check=False,
                        )
                    elif mode == "http_dependency_timeout_slo_v1":
                        command_result = subprocess.run(
                            ["sh", "-lc", "python3 -c \"import json; p='/etc/opsbench/dependency.json'; d=json.load(open(p)); d['delay_ms']=20; open(p,'w').write(json.dumps(d)); p='/etc/opsbench/app.json'; d=json.load(open(p)); d['dependency_timeout_ms']=500; open(p,'w').write(json.dumps(d))\"; /opt/opsbench/runtime/appctl.sh restart"],
                            capture_output=True, text=True, timeout=20, check=False,
                        )
                    elif mode == "linux_fd_leak_v1":
                        command_result = subprocess.run(
                            ["sh", "-lc", "python3 -c \"import json; p='/etc/opsbench/app.json'; d=json.load(open(p)); d['template_cache_scope']='request'; open(p,'w').write(json.dumps(d))\"; /opt/opsbench/runtime/appctl.sh restart"],
                            capture_output=True, text=True, timeout=20, check=False,
                        )
                    elif mode == "tls_hostname_mismatch_v1":
                        command_result = subprocess.run(
                            ["sh", "-lc", "openssl req -newkey rsa:2048 -nodes -subj '/CN=target' -keyout /etc/opsbench/tls/server.key -out /tmp/target.csr >/dev/null 2>&1; printf '%s\\n' 'subjectAltName=DNS:target' 'extendedKeyUsage=serverAuth' >/tmp/target.ext; openssl x509 -req -days 365 -sha256 -in /tmp/target.csr -CA /opt/opsbench/certs/ca.crt -CAkey /opt/opsbench/certs/ca.key -CAcreateserial -extfile /tmp/target.ext -out /etc/opsbench/tls/server.crt >/dev/null 2>&1; /opt/opsbench/runtime/appctl.sh restart"],
                            capture_output=True, text=True, timeout=30, check=False,
                        )
                    if command_result is not None and command_result.returncode != 0:
                        result = {"healthy": False, "error": command_result.stderr[-1000:] or "registered repair command failed"}
                    else:
                        state["mode"] = "baseline"
                        state["circuit"] = "closed"
                        if mode == "http_retry_circuit_breaker_v1":
                            state["override_dependency"] = "downstream"
                            state["effective_dependency"] = "downstream"
                            state["repair_epoch"] = int(state.get("repair_epoch") or 0) + 1
                        state.pop("repair_stage", None)
                        state_path.write_text(json.dumps(state), encoding="utf-8")
                        if mode == "kafka_consumer_lag_v1":
                            # Let the real consumer commit offsets after the
                            # state transition. The verifier checks the live
                            # group lag, not only the state file.
                            time.sleep(45)
                        result = {"healthy": True, "action": "restore_registered_service_state"}
            else:
                result = {"healthy": False, "error": "no public service repair is declared for this case"}
        except (OSError, urllib.error.URLError, subprocess.SubprocessError) as exc:
            result = {"healthy": False, "error": str(exc)}
        result["duration_sec"] = round(time.monotonic() - started, 4)
        _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "service_repair", "input": {"stage": stage, "action": action}, "result": result})
        return json.dumps(result, ensure_ascii=False)

    @tool
    def message_repair() -> str:
        """Apply the declared RabbitMQ resource-threshold repair through its control plane."""
        started = time.monotonic()
        result: dict[str, Any]
        try:
            # The Python runner does not contain rabbitmqctl and never gets a
            # Docker socket.  It places one bounded action request in the
            # public trace; the host-side runner executes only this registered
            # action in the declared broker service before verification.
            request_path = trace_dir / "agent_repair_requests.jsonl"
            _append_jsonl(request_path, {"action": "message_repair", "value": "set_disk_free_limit=50MB"})
            result = {"healthy": True, "status": {"queued": "message_repair"}}
        except OSError as exc:
            result = {"healthy": False, "status": {"error": str(exc)}}
        result["duration_sec"] = round(time.monotonic() - started, 4)
        _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "message_repair", "input": {}, "result": result})
        return json.dumps(result, ensure_ascii=False)

    @tool
    def diagnose() -> str:
        """Read a bounded, case-declared set of live operational signals."""
        started = time.monotonic()
        mode = os.environ.get("OPSBENCH_DIAGNOSTIC_MODE", "generic")
        commands = {
            "http_wrong_port_v1": (
                "printf 'config='; cat /runtime/server.conf 2>/dev/null || true; "
                "printf 'expected='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://target:8000/health; "
                "printf 'wrong='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://target:8080/health"
            ),
            "http_dependency_port_drift_v1": (
                "python3 -c \"import json; d=json.load(open('/etc/opsbench/app.json')); print(json.dumps({'dependency_host': d.get('dependency_host'), 'dependency_port': d.get('dependency_port')}))\"; "
                "printf 'override='; sed -n 's/^CATALOG_PORT=//p' /etc/opsbench/dependency.env 2>/dev/null || true; "
                "printf 'local_dependency='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:9001/catalog"
            ),
            "http_dependency_dns_poison_v1": (
                "python3 -c \"import json; d=json.load(open('/etc/opsbench/app.json')); print(json.dumps({'dependency_host': d.get('dependency_host'), 'dependency_port': d.get('dependency_port')}))\"; "
                "printf 'resolved='; getent ahostsv4 catalog.internal | awk 'NR==1 {print $1}'; "
                "printf 'local_dependency='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:9001/catalog; "
                "printf 'repair_target=hosts_mapping catalog.internal->127.0.0.1'"
            ),
            "http_dependency_timeout_slo_v1": (
                "python3 -c \"import json; a=json.load(open('/etc/opsbench/app.json')); d=json.load(open('/etc/opsbench/dependency.json')); print(json.dumps({'client_timeout_ms': a.get('dependency_timeout_ms'), 'dependency_delay_ms': d.get('delay_ms')}))\""
            ),
            "app_config_precedence_v1": (
                "python3 -c \"import json; print(json.dumps({'base_port': json.load(open('/etc/opsbench/app.json')).get('port'), 'override_present': __import__('os').path.exists('/etc/opsbench/app.env')}))\"; "
                "printf 'health='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/health"
            ),
            "linux_fd_leak_v1": (
                "printf 'app_pid='; cat /run/demo-app.pid 2>/dev/null || true; "
                "printf 'fd_count='; pid=$(cat /run/demo-app.pid 2>/dev/null || true); test -n \"$pid\" && find /proc/$pid/fd -mindepth 1 -maxdepth 1 2>/dev/null | wc -l || true; "
                "printf 'probe='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/report-template"
            ),
            "tls_hostname_mismatch_v1": (
                "printf 'verified='; curl -sS --cacert /etc/opsbench/ca.crt --max-time 3 -o /dev/null -w '%{http_code}' https://target:8443/health; "
                "printf 'insecure='; curl -ksS --max-time 3 -o /dev/null -w '%{http_code}' https://127.0.0.1:8443/health"
            ),
            "postgres_lock_contention_v1": (
                "printf 'lock_holders='; PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT count(*) FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid WHERE l.locktype='advisory' AND a.application_name='opsbench-lock-holder' AND l.granted;\"; "
                "printf 'orders_probe='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:18085/orders"
            ),
            "postgres_connection_pool_exhaustion_v1": (
                "printf 'pool_holders='; PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT count(*) FROM pg_stat_activity WHERE application_name='opsbench-pool-holder';\"; "
                "printf 'query_probe='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:18086/query"
            ),
            "redis_cache_corruption_v1": (
                "printf 'cache_payload='; redis-cli -h redis GET catalog:v1; "
                "printf 'catalog_probe='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:18087/catalog"
            ),
            "kafka_consumer_lag_v1": (
                "printf 'consumer_state='; python3 -c \"import json; print(json.load(open('/runtime/state.json')))\"; "
                "printf 'lag_probe='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:18088/lag; "
                "printf 'broker_metadata='; kcat -b kafka:9092 -L -t opsbench-events 2>/dev/null | head -n 8 || true"
            ),
            "http_retry_circuit_breaker_v1": (
                "printf 'business_probe='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:18089/business; "
                "printf 'downstream_probe='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://downstream:18090/data; "
                "printf 'circuit_state='; python3 -c \"import json; print(json.load(open('/runtime/state.json')))\""
            ),
            "app_config_precedence_v1": (
                "printf 'base_config='; python3 -c \"import json; print(json.load(open('/etc/opsbench/app.json')))\"; "
                "printf 'override='; if test -f /etc/opsbench/app.env; then cat /etc/opsbench/app.env; else printf 'absent'; fi; "
                "printf 'effective_health='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/health; "
                "printf 'reconciler='; pgrep -af config-reconciler.py || true"
            ),
        }
        candidate_actions = {
            "http_dependency_port_drift_v1": {
                "prepare": ["restore_dependency_port", "restart_caller", "edit_base_config"],
                "apply": ["restore_dependency_port", "restart_caller", "edit_base_config"],
            },
            "http_dependency_dns_poison_v1": {
                "prepare": ["restore_dns_mapping", "change_caller_contract", "restart_caller"],
                "apply": ["restore_dns_mapping", "change_caller_contract", "restart_caller"],
            },
            "http_dependency_timeout_slo_v1": {
                "prepare": ["restore_dependency_slo", "increase_timeout_only", "restart_caller"],
                "apply": ["restore_dependency_slo", "increase_timeout_only", "restart_caller"],
            },
            "http_retry_circuit_breaker_v1": {
                "prepare": ["restart_caller", "recover_dependency"],
                "apply": ["restart_caller", "recover_dependency"],
            },
            "app_config_precedence_v1": {
                "prepare": ["remove_environment_override", "restart_caller", "edit_generated_config"],
                "apply": ["remove_environment_override", "restart_caller", "edit_generated_config"],
            },
            "postgres_lock_contention_v1": {
                "prepare": ["restart_database", "terminate_lock_holders", "change_query_timeout"],
                "apply": ["restart_database", "terminate_lock_holders", "change_query_timeout"],
            },
            "postgres_connection_pool_exhaustion_v1": {
                "prepare": ["increase_max_connections", "release_pool_holders", "restart_database"],
                "apply": ["increase_max_connections", "release_pool_holders", "restart_database"],
            },
            "redis_cache_corruption_v1": {
                "prepare": ["delete_cache_key", "disable_validation", "rebuild_cache_payload"],
                "apply": ["delete_cache_key", "disable_validation", "rebuild_cache_payload"],
            },
            "kafka_consumer_lag_v1": {
                "prepare": ["restart_broker", "pause_producer", "reset_offsets"],
                "apply": ["reset_offsets", "increase_poll_timeout", "resume_consumer"],
            },
            "linux_fd_leak_v1": {
                "prepare": ["disable_template_fd_leak", "restart_service", "raise_nofile_limit"],
                "apply": ["disable_template_fd_leak", "restart_service", "raise_nofile_limit"],
            },
            "tls_hostname_mismatch_v1": {
                "prepare": ["restore_certificate_identity", "disable_tls_verification", "restart_service"],
                "apply": ["restore_certificate_identity", "disable_tls_verification", "restart_service"],
            },
        }
        command = commands.get(mode, "printf 'health='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/health")
        try:
            completed = subprocess.run(["/bin/sh", "-lc", command], capture_output=True, text=True, timeout=8, check=False)
            result = {
                "healthy": completed.returncode == 0,
                "status": {
                    "mode": mode,
                    "signals": (completed.stdout or "")[-6000:],
                    "stderr": (completed.stderr or "")[-2000:],
                    "candidate_actions": candidate_actions.get(mode, {}),
                },
                "duration_sec": round(time.monotonic() - started, 4),
            }
            try:
                (trace_dir / "agent_diagnosis.json").write_text(json.dumps({
                    "mode": mode,
                    "signals": result["status"].get("signals", ""),
                }), encoding="utf-8")
            except OSError:
                pass
        except (OSError, subprocess.SubprocessError) as exc:
            result = {"healthy": False, "status": {"mode": mode, "error": str(exc)}, "duration_sec": round(time.monotonic() - started, 4)}
        _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "diagnose", "input": {}, "result": result})
        return json.dumps(result, ensure_ascii=False)

    @tool
    def health_check() -> str:
        """Read the live service health signal after a repair."""
        started = time.monotonic()
        health_mode = os.environ.get("OPSBENCH_HEALTH_MODE", "status")
        if health_mode == "service":
            try:
                health_url = os.environ.get("OPSBENCH_HEALTH_URL", "http://127.0.0.1:8080/health")
                with urllib.request.urlopen(health_url, timeout=5) as response:
                    result = {
                        "healthy": response.status == 200,
                        "status": {"http_status": response.status, "url": health_url},
                        "duration_sec": round(time.monotonic() - started, 4),
                    }
            except (OSError, urllib.error.URLError) as exc:
                result = {"healthy": False, "status": {"error": str(exc)}, "duration_sec": round(time.monotonic() - started, 4)}
            _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "health_check", "input": {}, "result": result})
            return json.dumps(result, ensure_ascii=False)
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
        if health_mode == "url":
            url = os.environ.get("OPSBENCH_HEALTH_URL", "").strip()
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    result = {"healthy": response.status == 200, "status": {"http_status": response.status}, "duration_sec": round(time.monotonic() - started, 4)}
            except (OSError, urllib.error.URLError) as exc:
                result = {"healthy": False, "status": {"error": str(exc)}, "duration_sec": round(time.monotonic() - started, 4)}
            _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "health_check", "input": {}, "result": result})
            return json.dumps(result, ensure_ascii=False)
        if health_mode == "rabbitmq":
            try:
                status_code, body = _rabbitmq_get("/api/health/checks/alarms")
                result = {"healthy": status_code == 200, "status": {"http_status": status_code, "body": body[-2000:]}, "duration_sec": round(time.monotonic() - started, 4)}
            except (OSError, urllib.error.URLError, subprocess.SubprocessError) as exc:
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

    return [shell, business_check, diagnose, health_check, metrics_query, message_probe, service_repair, message_repair]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task")
    parser.add_argument("--tools")
    parser.add_argument("--trace")
    parser.add_argument("--case-dir")
    parser.add_argument("--work-dir")
    parser.add_argument("--timeout-sec", type=int, default=300)
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

    api_key = os.environ.get("OPSBENCH_API_KEY")
    base_url = os.environ.get("OPSBENCH_BASE_URL", "https://api.deepseek.com")
    model_name = os.environ.get("OPSBENCH_AGENT_MODEL") or os.environ.get("OPSBENCH_MODEL") or "deepseek-v4-flash"
    if not api_key:
        _write_json(trace_dir / "agent_result.json", {"passed": False, "error": "OPSBENCH_API_KEY is missing"})
        return 2

    tool_contract_text = json.dumps(public_tools, ensure_ascii=False, indent=2)
    system_prompt = f"""You are an operations repair agent running inside the target container.
Use a bounded evidence-driven loop: inspect the public business operation,
collect the smallest useful live diagnostic signal, form one root-cause
hypothesis, apply the smallest safe registered repair, and verify the public
operation again. Do not assume that a healthy process means the task is solved.

The available tools are case-scoped. Prefer diagnostic evidence over the task
wording when choosing among candidate actions. If a repair tool reports a
protocol or stage requirement, follow that returned protocol; otherwise do not
invent stages, commands, or opaque action identifiers. For a staged case, call
diagnose first, then call service_repair with stage=prepare and the selected
action, followed by stage=apply with the same action. Never create protocol
state files with shell or use a repair merely because it is available. The
final business check must demonstrate recovery and preserve the declared
service contract.

Do not implement repairs with arbitrary shell commands, edit service code,
start replacement sidecars, kill or replace PID 1, disable validation, or use
broad filesystem scans. If a diagnostic command is blocked, use the declared
diagnostic tool instead. Do not look for verifier, scenario, hidden labels,
case-root files, Docker sockets, host files, or host credentials. Finish only
after the public business operation is healthy and the required persistence or
restart boundary has been verified.

Use only the exact public tool contract below. Its enum values and required
arguments are authoritative. Do not invent service names, endpoints, keys,
views, fields, or action values. If a tool returns an allowlist error, stop
guessing and choose a value from this contract.

PUBLIC TOOL CONTRACT:
{tool_contract_text}"""
    model = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0,
        timeout=int(os.environ.get("OPSBENCH_REQUEST_TIMEOUT", "45")),
        max_retries=int(os.environ.get("OPSBENCH_MAX_RETRIES", "2")),
    )
    # Keep the credential in the model client only. Tool subprocesses inherit
    # the post-scrub environment and therefore cannot inspect the API key.
    os.environ.pop("OPSBENCH_API_KEY", None)
    agent = create_react_agent(model, build_tools(trace_dir), prompt=system_prompt)
    try:
        max_steps = max(1, int(os.environ.get("OPSBENCH_AGENT_MAX_STEPS", "30")))
        result = agent.invoke(
            {"messages": [("user", task)]},
            config={"recursion_limit": max_steps},
        )
        messages = result.get("messages", [])
        for index, message in enumerate(messages):
            content = getattr(message, "content", "")
            tool_calls = getattr(message, "tool_calls", None)
            _append_jsonl(trace_dir / "agent_messages.jsonl", {
                "index": index,
                "type": type(message).__name__,
                "content": content if isinstance(content, str) else str(content),
                "tool_calls": tool_calls or [],
            })
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
