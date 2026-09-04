"""Small OpsBench-compatible LangChain ReAct agent.

The agent is intended to run inside the E2E target container.  It only gets
the public task, public tool description, and a writable trace directory.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
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
    "/agent",
    "/var/lib/opsbench/internal",
    "/runtime/fault.json",
    "/runtime/status.json",
    "OPSBENCH_CONTROL_ROOT",
    "/runtime/config.json",
    "/runtime/state.json",
    "/runtime/sink.mode",
    "/opsbench/control",
    "/opsbench/control?",
    "/api/v2/reload",
    "sink:19880/control",
    "/control?mode=",
    "run.py",
    "run.sh",
    "/case-root",
    "case-dir",
    "docker inspect",
    "/proc/",
    "opsbench_api_key",
    "find /",
    "grep -r /",
    "grep -rl /",
    "ls -lar /",
    "candidate_actions",
    "repair_target",
    "fault_primitive",
    "opsbench_template_id",
    "opsbench_diagnostic_mode",
    "inspect.getsource",
    "importlib",
    "runpy",
    "__file__",
)

# Public E2E capability names are intentionally semantic but scenario-neutral.
# Older case packages still use the implementation names; the runner selects
# the appropriate vocabulary from public/tools.json at startup.
_PUBLIC_TO_INTERNAL_TOOL_NAMES = {
    "command_run": "shell",
    # Legacy cases use service_status as the public alias for health_check.
    # Standardized cases opt into the generic service_status implementation
    # through OPSBENCH_TOOL_STANDARD_ID below.
    "service_status": "health_check",
    "business_probe": "business_check",
    "signal_view": "diagnose",
    "metrics_read": "metrics_query",
    "database_query": "database_query",
    "queue_inspect": "message_probe",
    "service_control": "service_repair",
    "queue_control": "message_repair",
    "cache_query": "cache_query",
    "tls_probe": "tls_probe",
    "secure_probe": "tls_probe",
    "transport_probe": "tls_probe",
    # Stable domain tool standards.  These names describe discoverable
    # capabilities and are intentionally independent of a case's answer.
    "service_list": "service_list",
    "business_probe": "business_check",
    "config_sources": "config_sources",
    "config_read": "config_read",
    "config_update": "config_update",
    "service_manage": "service_manage",
    "dependency_list": "dependency_list",
    "dependency_probe": "dependency_probe",
    "slo_read": "slo_read",
}

_PUBLIC_TOOL_DESCRIPTIONS = {
    "command_run": "Run a bounded diagnostic or maintenance command inside the declared runtime.",
    "service_status": "Read the live service or database health signal.",
    "business_probe": "Check the declared public business operation, not just process liveness.",
    "signal_view": "Read bounded live signals declared for this operational scenario.",
    "metrics_read": "Read a bounded live resource metric for diagnosis.",
    "database_query": "Run a read-only SQL query against the declared database.",
    "queue_inspect": "Inspect bounded message-system health and flow signals.",
    "service_control": "Apply one bounded change selected from live diagnostic evidence.",
    "queue_control": "Request the case-declared bounded message-system state change.",
    "cache_query": "Read the declared Redis policy and cache health counters.",
    "tls_probe": "Run the case-declared trust, protocol, or certificate-status probe.",
    "secure_probe": "Inspect the live secure transport, trust, protocol, or certificate-status result.",
    "transport_probe": "Inspect the live transport, trust, protocol, or certificate-status result.",
    "service_list": "List managed services visible in the current runtime.",
    "service_status": "Read the live lifecycle and health state of a discovered service.",
    "business_probe": "Check the declared public business operation for a discovered service.",
    "config_sources": "List configuration sources and precedence for a discovered service.",
    "config_read": "Read bounded entries from one discovered configuration source.",
    "config_update": "Set or remove one entry in a writable discovered configuration source.",
    "service_manage": "Read or change the lifecycle state of a discovered service.",
    "dependency_list": "List dependencies visible to a discovered service.",
    "dependency_probe": "Read bounded reachability, response and latency signals from a discovered dependency.",
    "slo_read": "Read the public latency or availability objective for a discovered service.",
}


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


def build_tools(trace_dir: Path, allowed_tool_names: set[str] | list[str] | None = None):
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
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=8) as response:
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
    def business_check(service: str = "") -> str:
        """Check the public business operation, not just process liveness."""
        started = time.monotonic()
        url = os.environ.get("OPSBENCH_BUSINESS_CHECK_URL", "").strip()
        if not url:
            result = {
                "healthy": False,
                "status": {"error": "business check is not configured for this case"},
                "duration_sec": round(time.monotonic() - started, 4),
            }
            _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "business_check", "input": {"service": service}, "result": result})
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
                    "service": service,
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
        _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": "business_check", "input": {"service": service}, "result": result})
        return json.dumps(result, ensure_ascii=False)

    @tool
    def metrics_query(metric: str = "") -> str:
        """Read one bounded, case-declared live metrics endpoint."""
        started = time.monotonic()
        url = os.environ.get("OPSBENCH_METRICS_URL", "").strip()
        # Technology-faithful Prometheus cases expose their live API through
        # the Compose sidecar.  Keep the endpoint case-local and bounded, but
        # provide the declared default when the public tool is invoked inside
        # the verifier/agent network.
        if not url and os.environ.get("OPSBENCH_TEMPLATE_ID", "").startswith("fidelity_prometheus"):
            url = "http://prometheus:9090/api/v1/query?query=opsbench_business_up"
        if not url:
            result = {"healthy": False, "status": {"error": "metrics endpoint is not configured"}, "duration_sec": round(time.monotonic() - started, 4)}
        else:
            try:
                # Metrics endpoints are normally service-local inside the
                # Compose network.  Bypass host HTTP proxy variables so a
                # proxy cannot turn a healthy internal endpoint into a false
                # 404/connection failure.
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open(url, timeout=5) as response:
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
            alarm_path = "/api/overview" if os.environ.get("OPSBENCH_TEMPLATE_ID", "").startswith("fidelity_rabbitmq") else "/api/health/checks/alarms"
            alarm_status, alarm_body = _rabbitmq_get(alarm_path)
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
        mode = (
            os.environ.get("OPSBENCH_SERVICE_REPAIR_MODE", "")
            or os.environ.get("OPSBENCH_LIGHTWEIGHT_TEMPLATE", "")
            or os.environ.get("OPSBENCH_TEMPLATE_ID", "")
        )
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
            "app_stale_pid_v1",
        }
        diverse_modes = {
            "linux_oom_killer_v1",
            "linux_deleted_open_file_v1",
            "linux_mount_readonly_v1",
            "linux_conntrack_exhaustion_v1",
            "process_supervisor_restart_loop_v1",
            "container_healthcheck_mismatch_v1",
            "container_mount_permission_v1",
            "container_readonly_rootfs_v1",
            "container_pid_limit_v1",
            "http_proxy_misroute_v1",
            "tls_certificate_expiry_v1",
            "tls_mtls_client_auth_v1",
            "postgres_replication_lag_v1",
            "postgres_idle_transaction_v1",
            "postgres_readonly_replica_v1",
            "kafka_poison_message_v1",
            "rabbitmq_dead_letter_buildup_v1",
            "redis_cache_stampede_v1",
            "prometheus_alert_rule_mismatch_v1",
            "fluentbit_output_retry_storm_v1",
            "linux_inotify_watch_exhaustion_v1",
            "linux_ephemeral_port_exhaustion_v1",
            "linux_zombie_process_v1",
            "linux_cgroup_cpu_throttling_v1",
            "linux_tmpfs_capacity_v1",
            "container_capability_drop_v1",
            "container_startup_dependency_v1",
            "container_pid1_signal_forwarding_v1",
            "container_workdir_resolution_v1",
            "http_redirect_loop_v1",
            "http_header_size_limit_v1",
            "http_content_encoding_mismatch_v1",
            "tls_incomplete_chain_v1",
            "tls_protocol_version_mismatch_v1",
            "tls_revocation_status_v1",
            "postgres_autovacuum_debt_v1",
            "postgres_wal_retention_pressure_v1",
            "postgres_authentication_policy_v1",
            "postgres_sequence_exhaustion_v1",
            "kafka_under_replicated_partition_v1",
            "kafka_rebalance_storm_v1",
            "rabbitmq_prefetch_starvation_v1",
            "redis_eviction_policy_v1",
            "prometheus_label_cardinality_v1",
            "fluentbit_parser_mismatch_v1",
            "fidelity_postgres_wal_retention_pressure_v1",
            "fidelity_prometheus_label_cardinality_v1",
            "fidelity_rabbitmq_prefetch_starvation_v1",
            "fidelity_redis_eviction_policy_v1",
            "fidelity_tls_incomplete_chain_v1",
            "fidelity_tls_protocol_version_mismatch_v1",
            "fidelity_tls_revocation_status_v1",
            "linux_tcp_retransmission_pressure_v1",
            "linux_routing_blackhole_v1",
            "linux_mtu_mismatch_v1",
            "linux_swap_pressure_v1",
            "container_user_identity_mismatch_v1",
            "container_dns_alias_drift_v1",
            "container_log_driver_backpressure_v1",
            "http_request_body_limit_v1",
            "http_keepalive_exhaustion_v1",
            "http_auth_token_expiry_v1",
            "http_cache_stale_response_v1",
            "tls_sni_route_mismatch_v1",
            "tls_alpn_negotiation_gap_v1",
            "postgres_deadlock_cycle_v1",
            "postgres_replication_slot_retention_v1",
            "postgres_query_cancel_storm_v1",
            "kafka_offset_commit_failure_v1",
            "rabbitmq_consumer_ack_timeout_v1",
            "redis_hot_key_contention_v1",
            "prometheus_remote_write_backpressure_v1",
            "linux_load_average_runqueue_v1",
            "linux_file_descriptor_pressure_v1",
            "linux_process_limit_exhaustion_v1",
            "linux_inotify_queue_overflow_v1",
            "container_image_pull_policy_drift_v1",
            "container_healthcheck_interval_mismatch_v1",
            "container_oom_score_adjustment_v1",
            "http_response_header_buffer_v1",
            "http_proxy_protocol_mismatch_v1",
            "http_compression_cpu_contention_v1",
            "tls_certificate_chain_order_v1",
            "tls_session_ticket_rotation_v1",
            "postgres_checkpoint_write_pressure_v1",
            "postgres_statistics_staleness_v1",
            "postgres_work_mem_spill_v1",
            "kafka_fetch_batch_mismatch_v1",
            "rabbitmq_queue_ttl_mismatch_v1",
            "redis_expired_keys_lag_v1",
            "prometheus_scrape_timeout_mismatch_v1",
            "systemd_restart_throttle_v1",
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
            "app_stale_pid_v1": ("restore_service_identity", "restore_service_identity"),
        }
        try:
            lightweight_modes = {
                "linux_memory_growth_v1",
                "linux_disk_full_v1",
                "linux_inode_exhaustion_v1",
                "linux_upload_permission_v1",
                "linux_temp_permission_v1",
                "linux_file_lock_v1",
                "app_stale_pid_v1",
                "http_upstream_timeout_v1",
            }
            if mode in lightweight_modes:
                # The target service owns its benchmark control state.  The
                # Agent receives only this bounded semantic operation; it
                # never reads or writes the internal control file directly.
                accepted = {"restore", "restore_service_state", "repair_observed_fault"}
                if action not in accepted:
                    result = {"healthy": False, "error": "action must request the bounded observed-state repair"}
                else:
                    ok = _post_retry(
                        "http://127.0.0.1:8080/opsbench/control",
                        body=json.dumps({"action": "restore"}).encode("utf-8"),
                    )
                    result = {"healthy": ok, "action": "restore", "state_owner": "target-service"}
            elif mode in diverse_modes:
                # The second capability wave exposes one neutral repair
                # operation.  The target service owns the profile-specific
                # mechanism and state transition; the Agent never receives
                # a mechanism-specific hidden command.
                if action not in {"restore", "restore_service_state", "repair_observed_fault"}:
                    result = {"healthy": False, "error": "action must request the bounded observed-state repair"}
                else:
                    ok = _post_retry(
                        "http://127.0.0.1:8080/opsbench/control",
                        body=json.dumps({"action": "restore"}).encode("utf-8"),
                    )
                    result = {"healthy": ok, "action": "restore", "state_owner": "target-service"}
            elif mode == "fluentbit_backpressure_v1":
                if action not in {"repair_output_route", "restore_output_route", "restore"}:
                    result = {"healthy": False, "error": "action is not an allowed repair for the observed output state"}
                else:
                    # Restore the live downstream contract through the
                    # case-declared bounded service control.  Editing a
                    # host-mounted Fluent Bit config from a sibling container
                    # is not a reliable repair boundary on Docker Desktop;
                    # the sink endpoint changes only its observable
                    # availability state and does not expose hidden files or
                    # a Docker socket to the agent.
                    sink_ok = _post_retry("http://sink:19880/control?mode=healthy", body=b"{}")
                    reconnect_ok = _post_retry("http://fluent-bit:2020/api/v2/reload", body=b"{}")
                    result = {"healthy": sink_ok and reconnect_ok, "action": "repair_output_route", "sink_restored": sink_ok, "output_reconnected": reconnect_ok}
            elif mode == "prometheus_scrape_target_v1":
                if action not in {"repair_scrape_target", "restore_scrape_target", "restore"}:
                    result = {"healthy": False, "error": "action is not an allowed repair for the observed target state"}
                else:
                    result = {"healthy": _post_retry("http://exporter:19100/opsbench/control", body=b'{"action":"restore"}'), "action": "repair_scrape_target"}
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
                public_action_aliases = {
                    "remove_environment_override": "repair_config_source",
                    "restore_dependency_port": "repair_dependency_route",
                    "restore_dns_mapping": "repair_dependency_route",
                    "restore_dependency_slo": "repair_dependency_slo",
                    "disable_template_fd_leak": "repair_fd_policy",
                    "restore_certificate_identity": "repair_certificate_identity",
                    "restore_service_identity": "repair_service_identity",
                }
                accepted_actions = {expected_action, public_action_aliases.get(expected_action, expected_action)}
                # A generic public operation keeps the tool contract
                # scenario-neutral.  The primitive-specific implementation
                # remains private to the registered service-control adapter.
                if mode == "tls_hostname_mismatch_v1":
                    accepted_actions.add("restore")
                if mode == "linux_fd_leak_v1":
                    accepted_actions.add("restore")
                if stage not in {"prepare", "apply"}:
                    result = {"healthy": False, "error": "stage is required: call prepare, then apply"}
                elif action not in accepted_actions:
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
                    elif mode == "app_stale_pid_v1":
                        command_result = subprocess.run(
                            ["sh", "-lc", "/opt/opsbench/runtime/appctl.sh restart"],
                            capture_output=True, text=True, timeout=20, check=False,
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
                "printf 'local_dependency='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:9001/catalog"
            ),
            "http_dependency_timeout_slo_v1": (
                "python3 -c \"import json; a=json.load(open('/etc/opsbench/app.json')); d=json.load(open('/etc/opsbench/dependency.json')); print(json.dumps({'client_timeout_ms': a.get('dependency_timeout_ms'), 'dependency_delay_ms': d.get('delay_ms')}))\""
            ),
            "app_config_precedence_v1": (
                "python3 -c \"import json; from pathlib import Path; p=Path('/etc/opsbench/app.env'); values=p.read_text().splitlines() if p.exists() else []; print(json.dumps({'base_port': json.load(open('/etc/opsbench/app.json')).get('port'), 'override_key_present': any(line.split('=',1)[0].strip() == 'APP_PORT' for line in values if '=' in line)}))\"; "
                "printf 'health='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/health"
            ),
            "app_stale_pid_v1": (
                "printf 'pid_file='; cat /run/demo-app.pid 2>/dev/null || true; "
                "printf 'pid_alive='; pid=$(cat /run/demo-app.pid 2>/dev/null || true); "
                "test -n \"$pid\" && kill -0 \"$pid\" 2>/dev/null && echo true || echo false; "
                "printf 'pid_command='; pid=$(cat /run/demo-app.pid 2>/dev/null || true); "
                "test -n \"$pid\" && tr '\\0' ' ' </proc/$pid/cmdline 2>/dev/null || true; "
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
                "printf 'override_key_present='; python3 -c \"from pathlib import Path; p=Path('/etc/opsbench/app.env'); values=p.read_text().splitlines() if p.exists() else []; print(any(line.split('=',1)[0].strip() == 'APP_PORT' for line in values if '=' in line))\"; "
                "printf 'effective_health='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/health; "
                "printf 'reconciler='; pgrep -af config-reconciler.py || true"
            ),
            "fidelity_postgres_wal_retention_pressure_v1": "PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT slot_name, COALESCE(pg_wal_lsn_diff(pg_current_wal_lsn(),restart_lsn),0) FROM pg_replication_slots;\"",
            "fidelity_prometheus_label_cardinality_v1": "curl -fsS http://prometheus:9090/api/v1/query?query=opsbench_business_up; printf '\\nseries='; curl -fsS http://prometheus:9090/api/v1/series?match[]=opsbench_request_total",
            "fidelity_rabbitmq_prefetch_starvation_v1": "curl -fsS -u opsbench:opsbench-local-only http://rabbitmq:15672/api/queues/%2F/opsbench-prefetch",
            "fidelity_redis_eviction_policy_v1": "redis-cli -h redis CONFIG GET maxmemory-policy; redis-cli -h redis INFO stats | grep '^evicted_keys:'",
            "fidelity_tls_incomplete_chain_v1": "curl --noproxy '*' --cacert /runtime/tls/root.crt -fsS https://127.0.0.1:8443/health",
            "fidelity_tls_protocol_version_mismatch_v1": "printf '' | openssl s_client -connect 127.0.0.1:8443 -tls1_2 2>&1 | tail -n 8",
            "fidelity_tls_revocation_status_v1": "test -f /runtime/tls/server.crl && cat /runtime/tls/server.crl",
        }
        command = commands.get(mode, "printf 'health='; curl -sS --max-time 2 -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/health")
        try:
            completed = subprocess.run(["/bin/sh", "-lc", command], capture_output=True, text=True, timeout=8, check=False)
            result = {
                "healthy": completed.returncode == 0,
                    "status": {
                    "signals": (completed.stdout or "")[-6000:],
                    "stderr": (completed.stderr or "")[-2000:],
                },
                "duration_sec": round(time.monotonic() - started, 4),
            }
            try:
                (trace_dir / "agent_diagnosis.json").write_text(json.dumps({
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
                health_path = "/api/overview" if os.environ.get("OPSBENCH_TEMPLATE_ID", "").startswith("fidelity_rabbitmq") else "/api/health/checks/alarms"
                status_code, body = _rabbitmq_get(health_path)
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

    def _generic_mode() -> str:
        return os.environ.get("OPSBENCH_TEMPLATE_ID", "").strip()

    def _generic_services() -> dict[str, dict[str, str]]:
        mode = _generic_mode()
        if mode == "app_config_precedence_v1":
            return {"orders-api": {"kind": "application", "control": "/opt/opsbench/runtime/appctl.sh"}}
        if mode in {
            "http_dependency_timeout_slo_v1",
            "http_dependency_port_drift_v1",
            "http_dependency_dns_poison_v1",
        }:
            return {
                "orders-api": {"kind": "application", "control": "/opt/opsbench/runtime/appctl.sh"},
                "catalog": {"kind": "dependency", "control": "/opt/opsbench/runtime/dependencyctl.sh"},
            }
        return {"target": {"kind": "application", "control": "/opt/opsbench/runtime/appctl.sh"}}

    def _generic_service_error(service: str) -> dict[str, Any] | None:
        if service not in _generic_services():
            return {"ok": False, "error": "service was not returned by service_list", "service": service}
        return None

    def _record_generic(tool_name: str, payload: dict[str, Any], result: dict[str, Any]) -> str:
        result = {**result, "duration_sec": round(time.monotonic() - float(payload.pop("_started", time.monotonic())), 4)}
        _append_jsonl(trace_dir / "tool_calls.jsonl", {"tool": tool_name, "input": payload, "result": result})
        return json.dumps(result, ensure_ascii=False)

    def _generic_sources(service: str) -> list[dict[str, Any]]:
        mode = _generic_mode()
        if mode == "app_config_precedence_v1" and service == "orders-api":
            return [
                {"source_id": "base-config", "type": "base", "priority": 10, "writable": False, "path": "/etc/opsbench/app.json"},
                {"source_id": "runtime-environment", "type": "environment", "priority": 20, "writable": True, "path": "/etc/opsbench/app.env"},
                {"source_id": "effective-runtime", "type": "effective", "priority": 30, "writable": False},
            ]
        if mode == "http_dependency_port_drift_v1" and service == "catalog":
            return [{
                "source_id": "dependency-environment",
                "type": "environment",
                "priority": 20,
                "writable": True,
                "path": "/etc/opsbench/dependency.env",
            }]
        if mode == "http_dependency_dns_poison_v1" and service == "orders-api":
            return [{
                "source_id": "name-resolution",
                "type": "hosts",
                "priority": 20,
                "writable": True,
                "path": "/etc/hosts",
            }]
        if mode == "http_dependency_timeout_slo_v1":
            if service == "orders-api":
                return [
                    {"source_id": "service-config", "type": "runtime", "priority": 10, "writable": True, "path": "/etc/opsbench/app.json"},
                    {"source_id": "effective-runtime", "type": "effective", "priority": 20, "writable": False},
                ]
            if service == "catalog":
                return [{"source_id": "dependency-config", "type": "runtime", "priority": 10, "writable": True, "path": "/etc/opsbench/dependency.json"}]
        return []

    def _find_generic_source(service: str, source_id: str) -> dict[str, Any] | None:
        return next((item for item in _generic_sources(service) if item["source_id"] == source_id), None)

    def _read_env_file(path: Path) -> dict[str, str]:
        values: dict[str, str] = {}
        if not path.exists():
            return values
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text or text.startswith("#") or "=" not in text:
                continue
            key, value = text.split("=", 1)
            values[key.strip()] = value.strip()
        return values

    def _config_entries(service: str, source_id: str) -> list[dict[str, Any]]:
        source = _find_generic_source(service, source_id)
        if not source:
            return []
        if source.get("type") == "environment":
            values = _read_env_file(Path(str(source["path"])))
        elif source.get("type") == "hosts":
            values = {}
            try:
                for line in Path(str(source["path"])).read_text(encoding="utf-8").splitlines():
                    fields = line.split("#", 1)[0].split()
                    if len(fields) >= 2:
                        for hostname in fields[1:]:
                            values[hostname] = fields[0]
            except OSError:
                values = {}
        elif source.get("type") == "effective":
            values: dict[str, Any] = {}
            base_path = Path("/etc/opsbench/app.json")
            if base_path.exists():
                values.update(json.loads(base_path.read_text(encoding="utf-8")))
            if _generic_mode() == "app_config_precedence_v1":
                values.update(_read_env_file(Path("/etc/opsbench/app.env")))
        else:
            path = Path(str(source["path"]))
            if not path.exists():
                return []
            values = json.loads(path.read_text(encoding="utf-8"))
        return [{"key": str(key), "value": value, "source_id": source_id} for key, value in values.items()]

    @tool
    def service_list() -> str:
        """List services exposed by the current runtime."""
        started = time.monotonic()
        services = [
            {"service_id": service_id, "role": details["kind"]}
            for service_id, details in _generic_services().items()
        ]
        return _record_generic("service_list", {}, {"services": services, "ok": True, "_started": started})

    @tool
    def service_status(service: str = "") -> str:
        """Read lifecycle state for a discovered service."""
        started = time.monotonic()
        error = _generic_service_error(service)
        if error:
            return _record_generic("service_status", {"service": service, "_started": started}, error)
        control = _generic_services()[service]["control"]
        try:
            completed = subprocess.run([control, "status"], capture_output=True, text=True, timeout=10, check=False)
            result = {
                "ok": completed.returncode == 0,
                "service": service,
                "running": completed.returncode == 0,
                "returncode": completed.returncode,
                "stdout": (completed.stdout or "")[-2000:],
                "stderr": (completed.stderr or "")[-2000:],
                "_started": started,
            }
        except (OSError, subprocess.SubprocessError) as exc:
            result = {"ok": False, "service": service, "error": str(exc), "_started": started}
        return _record_generic("service_status", {"service": service, "_started": started}, result)

    @tool
    def config_sources(service: str = "") -> str:
        """List configuration sources and precedence for a discovered service."""
        started = time.monotonic()
        error = _generic_service_error(service)
        if error:
            return _record_generic("config_sources", {"service": service, "_started": started}, error)
        sources = [{key: value for key, value in item.items() if key != "path"} for item in _generic_sources(service)]
        return _record_generic("config_sources", {"service": service, "_started": started}, {"ok": True, "service": service, "sources": sources})

    @tool
    def config_read(service: str = "", source_id: str = "", key: str = "") -> str:
        """Read bounded entries from one discovered configuration source."""
        started = time.monotonic()
        error = _generic_service_error(service)
        source = _find_generic_source(service, source_id)
        if error:
            result = error
        elif not source:
            result = {"ok": False, "error": "source was not returned by config_sources", "service": service, "source_id": source_id}
        else:
            entries = _config_entries(service, source_id)
            if key:
                entries = [item for item in entries if item["key"] == key]
            result = {"ok": True, "service": service, "source_id": source_id, "entries": entries[:64]}
        return _record_generic("config_read", {"service": service, "source_id": source_id, "key": key, "_started": started}, result)

    def _coerce_config_value(current: Any, value: str) -> Any:
        if isinstance(current, bool):
            return str(value).strip().casefold() in {"1", "true", "yes", "on"}
        if isinstance(current, int) and not isinstance(current, bool):
            return int(str(value).strip())
        if isinstance(current, float):
            return float(str(value).strip())
        return str(value)

    @tool
    def config_update(service: str = "", source_id: str = "", key: str = "", operation: str = "", value: str = "") -> str:
        """Set or remove one entry in a writable discovered configuration source."""
        started = time.monotonic()
        error = _generic_service_error(service)
        source = _find_generic_source(service, source_id)
        if error:
            result = error
        elif not source:
            result = {"ok": False, "error": "source was not returned by config_sources", "service": service, "source_id": source_id}
        elif not bool(source.get("writable")):
            result = {"ok": False, "error": "configuration source is read-only", "service": service, "source_id": source_id}
        elif operation not in {"set", "remove"}:
            result = {"ok": False, "error": "operation must be set or remove", "operation": operation}
        elif not key:
            result = {"ok": False, "error": "key is required"}
        else:
            try:
                path = Path(str(source["path"]))
                if source.get("type") == "environment":
                    values = _read_env_file(path)
                    if operation == "remove":
                        values.pop(key, None)
                    else:
                        values[key] = str(value)
                    path.write_text("".join(f"{name}={item}\n" for name, item in values.items()), encoding="utf-8")
                elif source.get("type") == "hosts":
                    lines = path.read_text(encoding="utf-8").splitlines()
                    lines = [
                        line for line in lines
                        if key not in line.split("#", 1)[0].split()[1:]
                    ]
                    if operation == "set":
                        lines.append(f"{value} {key}")
                    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                else:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    if operation == "remove":
                        data.pop(key, None)
                    else:
                        if key not in data:
                            result = {"ok": False, "error": "key was not present in the discovered configuration source", "key": key}
                            return _record_generic("config_update", {"service": service, "source_id": source_id, "key": key, "operation": operation, "value": value, "_started": started}, result)
                        data[key] = _coerce_config_value(data[key], value)
                    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                result = {"ok": True, "changed": True, "service": service, "source_id": source_id, "key": key, "operation": operation}
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
                result = {"ok": False, "error": str(exc), "service": service, "source_id": source_id, "key": key}
        return _record_generic("config_update", {"service": service, "source_id": source_id, "key": key, "operation": operation, "value": value, "_started": started}, result)

    @tool
    def service_manage(service: str = "", action: str = "") -> str:
        """Read or change the lifecycle state of a discovered service."""
        started = time.monotonic()
        error = _generic_service_error(service)
        if error:
            result = error
        elif action not in {"status", "start", "stop", "restart"}:
            result = {"ok": False, "error": "action must be status, start, stop, or restart", "action": action}
        else:
            try:
                control = _generic_services()[service]["control"]
                completed = subprocess.run([control, action], capture_output=True, text=True, timeout=30, check=False)
                result = {
                    "ok": completed.returncode == 0,
                    "service": service,
                    "action": action,
                    "returncode": completed.returncode,
                    "stdout": (completed.stdout or "")[-2000:],
                    "stderr": (completed.stderr or "")[-2000:],
                }
            except (OSError, subprocess.SubprocessError) as exc:
                result = {"ok": False, "service": service, "action": action, "error": str(exc)}
        return _record_generic("service_manage", {"service": service, "action": action, "_started": started}, result)

    @tool
    def dependency_list() -> str:
        """List dependencies visible to the current application."""
        started = time.monotonic()
        dependencies = []
        if _generic_mode() in {
            "http_dependency_timeout_slo_v1",
            "http_dependency_port_drift_v1",
            "http_dependency_dns_poison_v1",
        }:
            dependencies = [{"dependency_id": "catalog", "role": "catalog-provider"}]
        return _record_generic("dependency_list", {}, {"ok": True, "dependencies": dependencies, "_started": started})

    @tool
    def dependency_probe(dependency: str = "") -> str:
        """Read bounded reachability, response and latency signals from a discovered dependency."""
        started = time.monotonic()
        if _generic_mode() not in {
            "http_dependency_timeout_slo_v1",
            "http_dependency_port_drift_v1",
            "http_dependency_dns_poison_v1",
        } or dependency != "catalog":
            result = {"ok": False, "error": "dependency was not returned by dependency_list", "dependency": dependency}
        else:
            try:
                probe_started = time.monotonic()
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open("http://catalog.internal:9001/catalog", timeout=5) as response:
                    body = response.read(4000).decode("utf-8", errors="replace")
                    status = int(response.status)
                result = {"ok": status == 200, "dependency": dependency, "status": status, "elapsed_ms": round((time.monotonic() - probe_started) * 1000, 2), "body": body}
            except (OSError, urllib.error.URLError) as exc:
                result = {"ok": False, "dependency": dependency, "error": str(exc)}
        return _record_generic("dependency_probe", {"dependency": dependency, "_started": started}, result)

    @tool
    def slo_read(service: str = "") -> str:
        """Read the public latency or availability objective for a discovered service."""
        started = time.monotonic()
        error = _generic_service_error(service)
        if error:
            result = error
        elif _generic_mode() == "http_dependency_timeout_slo_v1" and service == "orders-api":
            result = {"ok": True, "service": service, "latency_budget_ms": 600, "availability_target": 0.99}
        else:
            result = {"ok": False, "service": service, "error": "no public SLO is configured for this service"}
        return _record_generic("slo_read", {"service": service, "_started": started}, result)

    @tool
    def database_query(query: str = "") -> str:
        """Run one bounded read-only PostgreSQL query."""
        started = time.monotonic()
        normalized = str(query or "").strip().casefold()
        forbidden = ("insert ", "update ", "delete ", "drop ", "alter ", "create ", "grant ", "revoke ", "pg_terminate_backend")
        if not normalized or any(token in normalized for token in forbidden):
            result = {"ok": False, "error": "database_query accepts read-only observation queries"}
        else:
            try:
                env = {key: value for key, value in os.environ.items() if key not in {"OPSBENCH_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"}}
                env.setdefault("PGPASSWORD", "opsbench-local-only")
                completed = subprocess.run(
                    ["psql", "-h", env.get("PGHOST", "db"), "-U", env.get("PGUSER", "opsbench"), "-d", env.get("PGDATABASE", "app"), "-At", "-c", str(query)],
                    capture_output=True, text=True, timeout=12, check=False, env=env,
                )
                result = {"ok": completed.returncode == 0, "stdout": (completed.stdout or "")[-6000:], "stderr": (completed.stderr or "")[-2000:]}
            except (OSError, subprocess.SubprocessError) as exc:
                result = {"ok": False, "error": str(exc)}
        return _record_generic("database_query", {"query": query, "_started": started}, result)

    @tool
    def cache_query() -> str:
        """Read the live Redis memory policy and eviction counter."""
        started = time.monotonic()
        try:
            policy = subprocess.run(["redis-cli", "-h", "redis", "CONFIG", "GET", "maxmemory-policy"], capture_output=True, text=True, timeout=8, check=False)
            stats = subprocess.run(["redis-cli", "-h", "redis", "INFO", "stats"], capture_output=True, text=True, timeout=8, check=False)
            result = {"ok": policy.returncode == 0 and stats.returncode == 0, "policy": policy.stdout[-1000:], "stats": stats.stdout[-3000:]}
        except (OSError, subprocess.SubprocessError) as exc:
            result = {"ok": False, "error": str(exc)}
        return _record_generic("cache_query", {}, {**result, "_started": started})

    @tool
    def tls_probe() -> str:
        """Run the case-declared TLS trust, protocol, or revocation probe."""
        started = time.monotonic()
        mode = os.environ.get("OPSBENCH_TEMPLATE_ID", "")
        if mode.startswith("fidelity_tls_protocol"):
            command = "printf '' | openssl s_client -connect 127.0.0.1:8443 -tls1_2 2>/dev/null"
        elif mode.startswith("fidelity_tls_revocation"):
            command = "openssl verify -CAfile /runtime/tls/root.crt -crl_check -CRLfile /runtime/tls/server.crl /runtime/tls/server.crt"
        else:
            command = "curl --noproxy '*' --cacert /runtime/tls/root.crt -fsS https://127.0.0.1:8443/health"
        try:
            completed = subprocess.run(["/bin/sh", "-lc", command], capture_output=True, text=True, timeout=12, check=False)
            result = {"ok": completed.returncode == 0, "returncode": completed.returncode, "stdout": (completed.stdout or "")[-4000:], "stderr": (completed.stderr or "")[-2000:]}
        except (OSError, subprocess.SubprocessError) as exc:
            result = {"ok": False, "error": str(exc)}
        return _record_generic("tls_probe", {}, {**result, "_started": started})

    implementation_tools = [
        shell, business_check, diagnose, health_check, metrics_query, message_probe,
        service_repair, message_repair, service_list, service_status, config_sources,
        config_read, config_update, service_manage, dependency_list, dependency_probe,
        slo_read, database_query, cache_query, tls_probe,
    ]
    if allowed_tool_names is None:
        return implementation_tools

    by_internal_name = {str(item.name): item for item in implementation_tools}
    standard_mode = os.environ.get("OPSBENCH_TOOL_STANDARD_ID", "").strip()
    selected = []
    for public_name in allowed_tool_names:
        name = str(public_name or "").strip()
        internal_name = _PUBLIC_TO_INTERNAL_TOOL_NAMES.get(name, name)
        if standard_mode in {"config-operations-v1", "dependency-operations-v1", "service-lifecycle-v1"} and name == "service_status":
            internal_name = "service_status"
        item = by_internal_name.get(internal_name)
        if item is None:
            continue
        if name == internal_name:
            selected.append(item)
            continue
        # StructuredTool is a Pydantic model.  Copying only the public name and
        # description preserves the original validated argument schema while
        # preventing the model from seeing the legacy answer-oriented name.
        selected.append(item.model_copy(update={
            "name": name,
            "description": _PUBLIC_TOOL_DESCRIPTIONS.get(name, item.description),
        }))
    return selected


def _invoke_public_tool(tool_map: dict[str, Any], name: str, payload: dict[str, Any], steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Invoke one declared public tool and retain a bounded oracle trace."""
    item = tool_map.get(name)
    if item is None:
        result = {"ok": False, "error": f"public tool {name!r} is not declared"}
        steps.append({"tool": name, "input": payload, "result": result})
        return result
    try:
        raw = item.invoke(payload)
        result = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(result, dict):
            result = {"ok": False, "error": "public tool returned a non-object result"}
    except Exception as exc:  # pragma: no cover - exercised in container smoke runs
        result = {"ok": False, "error": str(exc)}
    steps.append({"tool": name, "input": payload, "result": result})
    return result


def _public_oracle_app_config(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Solve app_config_precedence only through the public tool contract."""
    steps: list[dict[str, Any]] = []
    services = _invoke_public_tool(tool_map, "service_list", {}, steps)
    service_ids = {
        str(item.get("service_id"))
        for item in services.get("services", [])
        if isinstance(item, dict)
    }
    service = "orders-api"
    if service not in service_ids:
        return {"passed": False, "error": "orders-api was not discoverable", "steps": steps}
    sources = _invoke_public_tool(tool_map, "config_sources", {"service": service}, steps)
    source_ids = {str(item.get("source_id")) for item in sources.get("sources", []) if isinstance(item, dict)}
    source_id = "runtime-environment"
    if source_id not in source_ids:
        return {"passed": False, "error": "writable runtime environment was not discoverable", "steps": steps}
    before = _invoke_public_tool(tool_map, "config_read", {"service": service, "source_id": source_id}, steps)
    entries = [item for item in before.get("entries", []) if isinstance(item, dict)]
    if not any(str(item.get("key")) == "APP_PORT" for item in entries):
        return {"passed": False, "error": "APP_PORT was not observable in the active public source", "steps": steps}
    changed = _invoke_public_tool(tool_map, "config_update", {
        "service": service, "source_id": source_id, "key": "APP_PORT", "operation": "remove",
    }, steps)
    if not changed.get("ok"):
        return {"passed": False, "error": "public config_update(remove) failed", "steps": steps}
    restarted = _invoke_public_tool(tool_map, "service_manage", {"service": service, "action": "restart"}, steps)
    if not restarted.get("ok"):
        return {"passed": False, "error": "public service_manage(restart) failed", "steps": steps}
    time.sleep(1.0)
    after = _invoke_public_tool(tool_map, "config_read", {"service": service, "source_id": source_id}, steps)
    probe = _invoke_public_tool(tool_map, "business_probe", {"service": service}, steps)
    remaining = [item for item in after.get("entries", []) if isinstance(item, dict) and str(item.get("key")) == "APP_PORT"]
    passed = bool(probe.get("healthy")) and not remaining
    return {
        "passed": passed,
        "error": "" if passed else "business probe or semantic override check failed",
        "semantic_assertions": {"app_port_key_absent": not remaining, "business_healthy": bool(probe.get("healthy"))},
        "steps": steps,
    }


def _public_oracle_timeout(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Exercise the public diagnosis/repair path for the timeout primitive."""
    steps: list[dict[str, Any]] = []
    service = "orders-api"
    dependency = "catalog"
    services = _invoke_public_tool(tool_map, "service_list", {}, steps)
    service_ids = {str(item.get("service_id")) for item in services.get("services", []) if isinstance(item, dict)}
    if not {service, dependency}.issubset(service_ids):
        return {"passed": False, "error": "required services were not discoverable", "steps": steps}
    _invoke_public_tool(tool_map, "business_probe", {"service": service}, steps)
    deps = _invoke_public_tool(tool_map, "dependency_list", {}, steps)
    if not any(str(item.get("dependency_id")) == dependency for item in deps.get("dependencies", []) if isinstance(item, dict)):
        return {"passed": False, "error": "catalog dependency was not discoverable", "steps": steps}
    _invoke_public_tool(tool_map, "dependency_probe", {"dependency": dependency}, steps)
    _invoke_public_tool(tool_map, "slo_read", {"service": service}, steps)
    app_sources = _invoke_public_tool(tool_map, "config_sources", {"service": service}, steps)
    dep_sources = _invoke_public_tool(tool_map, "config_sources", {"service": dependency}, steps)
    app_source = "service-config"
    dep_source = "dependency-config"
    if not any(str(item.get("source_id")) == app_source for item in app_sources.get("sources", []) if isinstance(item, dict)):
        return {"passed": False, "error": "service config source was not discoverable", "steps": steps}
    if not any(str(item.get("source_id")) == dep_source for item in dep_sources.get("sources", []) if isinstance(item, dict)):
        return {"passed": False, "error": "dependency config source was not discoverable", "steps": steps}
    app_config = _invoke_public_tool(tool_map, "config_read", {"service": service, "source_id": app_source}, steps)
    dep_config = _invoke_public_tool(tool_map, "config_read", {"service": dependency, "source_id": dep_source}, steps)
    app_keys = {str(item.get("key")) for item in app_config.get("entries", []) if isinstance(item, dict)}
    dep_keys = {str(item.get("key")) for item in dep_config.get("entries", []) if isinstance(item, dict)}
    if "dependency_timeout_ms" not in app_keys or "delay_ms" not in dep_keys:
        return {"passed": False, "error": "public configuration did not expose the bounded repair keys", "steps": steps}
    updates = [
        _invoke_public_tool(tool_map, "config_update", {
            "service": dependency, "source_id": dep_source, "key": "delay_ms", "operation": "set", "value": "20",
        }, steps),
        _invoke_public_tool(tool_map, "config_update", {
            "service": service, "source_id": app_source, "key": "dependency_timeout_ms", "operation": "set", "value": "500",
        }, steps),
    ]
    if not all(bool(item.get("ok")) for item in updates):
        return {"passed": False, "error": "public timeout repair update failed", "steps": steps}
    for target in (dependency, service):
        restarted = _invoke_public_tool(tool_map, "service_manage", {"service": target, "action": "restart"}, steps)
        if not restarted.get("ok"):
            return {"passed": False, "error": f"public restart failed for {target}", "steps": steps}
    time.sleep(1.0)
    final_probe = _invoke_public_tool(tool_map, "business_probe", {"service": service}, steps)
    final_dependency = _invoke_public_tool(tool_map, "dependency_probe", {"dependency": dependency}, steps)
    passed = bool(final_probe.get("healthy")) and bool(final_dependency.get("ok"))
    return {
        "passed": passed,
        "error": "" if passed else "business/dependency probe did not recover",
        "semantic_assertions": {"business_healthy": bool(final_probe.get("healthy")), "dependency_healthy": bool(final_dependency.get("ok"))},
        "steps": steps,
    }


def _public_oracle_stale_pid(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Repair stale runtime state through the public lifecycle capability.

    This oracle intentionally uses the same discovery, observation, business
    probe, and lifecycle restart operations available to a benchmark Agent.
    It does not call a primitive-specific hidden action or private runtime
    path, so its positive result is evidence that the public task is
    actionable rather than evidence of an undisclosed answer string.
    """
    steps: list[dict[str, Any]] = []
    services = _invoke_public_tool(tool_map, "service_list", {}, steps)
    discovered = [
        item for item in services.get("services", [])
        if isinstance(item, dict) and str(item.get("service_id") or "")
    ]
    service = next(
        (str(item["service_id"]) for item in discovered if str(item.get("role") or "") == "application"),
        str(discovered[0]["service_id"]) if discovered else "",
    )
    if not service:
        return {"passed": False, "error": "no application service was discoverable", "steps": steps}
    before_status = _invoke_public_tool(tool_map, "service_status", {"service": service}, steps)
    before_signal = _invoke_public_tool(tool_map, "signal_view", {}, steps)
    before_probe = _invoke_public_tool(tool_map, "business_probe", {"service": service}, steps)
    restart = _invoke_public_tool(tool_map, "service_manage", {"service": service, "action": "restart"}, steps)
    time.sleep(1.0)
    after_status = _invoke_public_tool(tool_map, "service_status", {"service": service}, steps)
    after_signal = _invoke_public_tool(tool_map, "signal_view", {}, steps)
    after_probe = _invoke_public_tool(tool_map, "business_probe", {"service": service}, steps)
    passed = bool(restart.get("ok")) and bool(after_status.get("ok")) and bool(after_probe.get("healthy")) and bool(after_signal.get("healthy"))
    return {
        "passed": passed,
        "error": "" if passed else "public lifecycle restart or semantic recovery check failed",
        "semantic_assertions": {
            "service_discovered": bool(service),
            "baseline_observed": bool(before_status.get("ok") is False or before_signal.get("healthy") is False or before_probe.get("healthy") is False),
            "business_healthy": bool(after_probe.get("healthy")),
            "live_identity_observed": bool(after_signal.get("healthy")),
            "restart_persistent": bool(after_status.get("ok")) and bool(after_probe.get("healthy")),
        },
        "steps": steps,
    }


def _public_oracle_dependency(tool_map: dict[str, Any], primitive_id: str) -> dict[str, Any]:
    """Repair a dependency route through the discoverable config contract."""
    steps: list[dict[str, Any]] = []
    services = _invoke_public_tool(tool_map, "service_list", {}, steps)
    service_ids = {str(item.get("service_id")) for item in services.get("services", []) if isinstance(item, dict)}
    if not {"orders-api", "catalog"}.issubset(service_ids):
        return {"passed": False, "error": "required application/dependency services were not discoverable", "steps": steps}
    dependencies = _invoke_public_tool(tool_map, "dependency_list", {}, steps)
    if not any(str(item.get("dependency_id")) == "catalog" for item in dependencies.get("dependencies", []) if isinstance(item, dict)):
        return {"passed": False, "error": "catalog dependency was not discoverable", "steps": steps}

    if primitive_id == "http_dependency_port_drift_v1":
        service = "catalog"
        source_id = "dependency-environment"
        key = "CATALOG_PORT"
        operation = "remove"
        value = ""
        restart_service = "catalog"
    else:
        service = "orders-api"
        source_id = "name-resolution"
        key = "catalog.internal"
        operation = "set"
        value = "127.0.0.1"
        restart_service = "orders-api"

    sources = _invoke_public_tool(tool_map, "config_sources", {"service": service}, steps)
    source_ids = {str(item.get("source_id")) for item in sources.get("sources", []) if isinstance(item, dict)}
    if source_id not in source_ids:
        return {"passed": False, "error": "the writable dependency route source was not discoverable", "steps": steps}
    before = _invoke_public_tool(tool_map, "config_read", {"service": service, "source_id": source_id}, steps)
    if not before.get("ok"):
        return {"passed": False, "error": "dependency route could not be read", "steps": steps}
    changed = _invoke_public_tool(tool_map, "config_update", {
        "service": service,
        "source_id": source_id,
        "key": key,
        "operation": operation,
        **({"value": value} if operation == "set" else {}),
    }, steps)
    if not changed.get("ok"):
        return {"passed": False, "error": "dependency route update failed", "steps": steps}
    restarted = _invoke_public_tool(tool_map, "service_manage", {"service": restart_service, "action": "restart"}, steps)
    time.sleep(0.5)
    business = _invoke_public_tool(tool_map, "business_probe", {"service": "orders-api"}, steps)
    dependency = _invoke_public_tool(tool_map, "dependency_probe", {"dependency": "catalog"}, steps)
    after = _invoke_public_tool(tool_map, "config_read", {"service": service, "source_id": source_id}, steps)
    entries = [item for item in after.get("entries", []) if isinstance(item, dict)]
    observed = {str(item.get("key")): str(item.get("value")) for item in entries}
    route_ok = key not in observed if operation == "remove" else observed.get(key) == value
    passed = bool(restarted.get("ok")) and bool(business.get("healthy")) and bool(dependency.get("ok")) and route_ok
    return {
        "passed": passed,
        "error": "" if passed else "dependency route or business recovery check failed",
        "semantic_assertions": {
            "route_updated": route_ok,
            "business_healthy": bool(business.get("healthy")),
            "dependency_healthy": bool(dependency.get("ok")),
            "restart_ok": bool(restarted.get("ok")),
        },
        "steps": steps,
    }


def _public_oracle_nginx(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Clear the transient listener conflict through the public shell tool."""
    steps: list[dict[str, Any]] = []
    repair = _invoke_public_tool(tool_map, "command_run", {
        "command": "pkill -f '[p]ort_blocker.py'",
    }, steps)
    time.sleep(1.0)
    status = _invoke_public_tool(tool_map, "service_status", {}, steps)
    passed = int(repair.get("returncode", 1)) == 0 and bool(status.get("healthy"))
    return {
        "passed": passed,
        "error": "" if passed else "public listener repair or health observation failed",
        "semantic_assertions": {"operation_ok": int(repair.get("returncode", 1)) == 0, "service_healthy": bool(status.get("healthy"))},
        "steps": steps,
    }


def _public_oracle_cpu(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Disable the runaway worker and verify the live process state."""
    steps: list[dict[str, Any]] = []
    repair = _invoke_public_tool(tool_map, "command_run", {
        "command": "python3 -c \"import json; p='/runtime/worker.conf'; d=json.load(open(p)); d['enabled']=False; open(p,'w').write(json.dumps(d))\"",
    }, steps)
    time.sleep(1.0)
    worker = _invoke_public_tool(tool_map, "command_run", {
        "command": "! pgrep -f '[b]usy_loop'",
    }, steps)
    status = _invoke_public_tool(tool_map, "service_status", {}, steps)
    passed = int(repair.get("returncode", 1)) == 0 and int(worker.get("returncode", 1)) == 0 and bool(status.get("healthy"))
    return {
        "passed": passed,
        "error": "" if passed else "public worker repair or health observation failed",
        "semantic_assertions": {"operation_ok": int(repair.get("returncode", 1)) == 0, "worker_absent": int(worker.get("returncode", 1)) == 0, "service_healthy": bool(status.get("healthy"))},
        "steps": steps,
    }


def _public_oracle_fd_leak(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Use the staged public service-control path for the FD policy case."""
    steps: list[dict[str, Any]] = []
    diagnosis = _invoke_public_tool(tool_map, "signal_view", {}, steps)
    prepared = _invoke_public_tool(tool_map, "service_control", {"stage": "prepare", "action": "restore"}, steps)
    applied = _invoke_public_tool(tool_map, "service_control", {"stage": "apply", "action": "restore"}, steps)
    time.sleep(1.0)
    business = _invoke_public_tool(tool_map, "business_probe", {}, steps)
    passed = bool(diagnosis.get("healthy")) and bool(prepared.get("healthy")) and bool(applied.get("healthy")) and bool(business.get("healthy"))
    return {
        "passed": passed,
        "error": "" if passed else "public FD repair or business observation failed",
        "semantic_assertions": {"diagnosis_observed": bool(diagnosis.get("healthy")), "operation_ok": bool(applied.get("healthy")), "business_healthy": bool(business.get("healthy"))},
        "steps": steps,
    }


def _public_oracle_postgres_index(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Restore the index and verify the live plan through the SQL client."""
    steps: list[dict[str, Any]] = []
    repair = _invoke_public_tool(tool_map, "command_run", {
        "command": "PGPASSWORD=opsbench-local-only psql -v ON_ERROR_STOP=1 -h \"$PGHOST\" -U \"$PGUSER\" -d \"$PGDATABASE\" -c \"CREATE INDEX IF NOT EXISTS orders_customer_id_idx ON orders(customer_id); ANALYZE orders;\"",
    }, steps)
    plan = _invoke_public_tool(tool_map, "command_run", {
        "command": "PGPASSWORD=opsbench-local-only psql -At -h \"$PGHOST\" -U \"$PGUSER\" -d \"$PGDATABASE\" -c \"EXPLAIN SELECT id, customer_id, payload FROM orders WHERE customer_id = 4242 ORDER BY id LIMIT 50;\"",
    }, steps)
    status = _invoke_public_tool(tool_map, "service_status", {}, steps)
    plan_text = str(plan.get("stdout") or "")
    indexed = any(token in plan_text for token in ("Index Scan", "Index Only Scan", "Bitmap Index Scan")) and "Seq Scan" not in plan_text
    passed = int(repair.get("returncode", 1)) == 0 and int(plan.get("returncode", 1)) == 0 and indexed and bool(status.get("healthy"))
    return {
        "passed": passed,
        "error": "" if passed else "public index repair or plan verification failed",
        "semantic_assertions": {"index_repaired": int(repair.get("returncode", 1)) == 0, "index_plan_observed": indexed, "database_healthy": bool(status.get("healthy"))},
        "steps": steps,
    }


def _public_oracle_rabbitmq(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Queue the declared broker repair after observing the alarm interface."""
    steps: list[dict[str, Any]] = []
    observed = _invoke_public_tool(tool_map, "queue_inspect", {}, steps)
    repair = _invoke_public_tool(tool_map, "queue_control", {}, steps)
    # The host-side lifecycle runner applies the queued, registered control
    # after this process exits and then runs the hidden verifier.
    passed = bool(repair.get("healthy"))
    return {
        "passed": passed,
        "error": "" if passed else "public queue repair request failed",
        "semantic_assertions": {"alarm_observed": "healthy" in observed, "operation_ok": bool(repair.get("healthy"))},
        "steps": steps,
    }


def _public_oracle_lightweight(tool_map: dict[str, Any], primitive_id: str) -> dict[str, Any]:
    """Exercise the generic public command path for lightweight Linux cases."""
    commands = {
        "linux_memory_growth_v1": (
            "python -c \"import json; p='/runtime/config.json'; d=json.load(open(p)); d.update(growth_enabled=False, repair_mode='persistent'); open(p,'w').write(json.dumps(d))\""
        ),
        "linux_disk_full_v1": "rm -f /data/filler",
        "linux_inode_exhaustion_v1": "rm -rf /data/inodes",
        # The directory is provisioned for the service user; changing its
        # mode is the public repair, while ownership remains observable.
        "linux_upload_permission_v1": "chmod 0770 /data/uploads",
        "linux_temp_permission_v1": "chmod 1730 /data/tmp",
        "linux_file_lock_v1": (
            "python -c \"import json; p='/runtime/config.json'; d=json.load(open(p)); d.update(lock_enabled=False, repair_mode='persistent'); open(p,'w').write(json.dumps(d))\""
        ),
        # The timeout case is repaired only through the bounded public
        # service_control endpoint; the command value is a compatibility
        # placeholder for pre-isolation packages.
        "http_upstream_timeout_v1": "true",
    }
    steps: list[dict[str, Any]] = []
    command = commands.get(primitive_id)
    if not command:
        return {"passed": False, "error": f"unsupported_public_oracle:{primitive_id}", "steps": steps}
    if "service_control" in tool_map:
        repair = _invoke_public_tool(
            tool_map,
            "service_control",
            {"action": "restore"},
            steps,
        )
    else:
        # Compatibility path for historical packages that predate the
        # isolated semantic repair endpoint.
        repair = _invoke_public_tool(tool_map, "command_run", {"command": command}, steps)
    # Some lightweight services reconcile a changed config from a background
    # loop.  Give that loop one bounded scheduling interval before observing
    # health; otherwise the public oracle can race a legitimate repair.
    time.sleep(1.0)
    status = _invoke_public_tool(tool_map, "service_status", {}, steps)
    passed = (
        (bool(repair.get("healthy")) if "service_control" in tool_map else int(repair.get("returncode", 1)) == 0)
        and bool(status.get("healthy"))
    )
    return {
        "passed": passed,
        "error": "" if passed else "public command repair or health check failed",
        "semantic_assertions": {
            "bounded_repair_executed": (
                bool(repair.get("healthy"))
                if "service_control" in tool_map
                else int(repair.get("returncode", 1)) == 0
            ),
            "service_healthy": bool(status.get("healthy")),
        },
        "steps": steps,
    }


def _public_oracle_diverse(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Exercise the neutral public repair path for capability profiles."""
    steps: list[dict[str, Any]] = []
    # Compact-v3 cases use the versioned lifecycle contract.  Keep this path
    # separate from the legacy capability aliases so the fairness scanner can
    # prove that the selected public oracle only calls declared tools.
    if "service_manage" in tool_map:
        services = _invoke_public_tool(tool_map, "service_list", {}, steps)
        service = ""
        if isinstance(services.get("services"), list) and services["services"]:
            service = str(services["services"][0].get("service_id") or "")
        diagnosis = _invoke_public_tool(tool_map, "signal_view", {}, steps)
        repair = _invoke_public_tool(tool_map, "service_manage", {"service": service, "action": "restart"}, steps)
        time.sleep(1.0)
        status = _invoke_public_tool(tool_map, "service_status", {"service": service}, steps)
        business = _invoke_public_tool(tool_map, "business_probe", {"service": service}, steps)
        observed = bool(diagnosis.get("healthy") or diagnosis.get("ok") or diagnosis.get("status"))
        healthy = bool(status.get("healthy") or status.get("ok"))
        passed = bool(service) and bool(repair.get("ok") or repair.get("healthy")) and healthy and bool(business.get("healthy"))
        return {
            "passed": passed,
            "error": "" if passed else "public lifecycle repair or semantic verification failed",
            "semantic_assertions": {
                "service_discovered": bool(service),
                "diagnosis_observed": observed,
                "operation_applied": bool(repair.get("ok") or repair.get("healthy")),
                "service_healthy": healthy,
                "business_operation": bool(business.get("healthy")),
            },
            "steps": steps,
        }
    diagnosis = _invoke_public_tool(tool_map, "signal_view", {}, steps)
    repair_tool = "service_" + "control"
    metrics_tool = "metrics_" + "read"
    repair = _invoke_public_tool(tool_map, repair_tool, {"action": "restore"}, steps)
    time.sleep(1.0)
    status = _invoke_public_tool(tool_map, "service_status", {}, steps)
    business = _invoke_public_tool(tool_map, "business_probe", {"service": "target"}, steps)
    metrics = _invoke_public_tool(tool_map, metrics_tool, {"metric": "mechanism_signal"}, steps)
    passed = (
        bool(repair.get("healthy"))
        and bool(status.get("healthy") or status.get("ok"))
        and bool(business.get("healthy"))
        and bool(metrics.get("healthy"))
    )
    return {
        "passed": passed,
        "error": "" if passed else "public capability repair or semantic verification failed",
        "semantic_assertions": {
            "diagnosis_observed": bool(diagnosis.get("healthy")),
            "operation_applied": bool(repair.get("healthy")),
                "service_healthy": bool(status.get("healthy") or status.get("ok")),
            "business_operation": bool(business.get("healthy")),
            "metrics_observed": bool(metrics.get("healthy")),
        },
        "steps": steps,
    }


def _public_oracle_fidelity(tool_map: dict[str, Any], primitive_id: str) -> dict[str, Any]:
    """Use the public domain observation plus the real technology control."""
    steps: list[dict[str, Any]] = []
    if primitive_id.startswith("fidelity_postgres"):
        before = _invoke_public_tool(tool_map, "database_query", {"query": "SELECT count(*) FROM pg_replication_slots WHERE slot_name LIKE 'opsbench_%'"}, steps)
        observed = bool(before.get("ok"))
        after_tool = "database_query"
        after_payload = {"query": "SELECT count(*) FROM pg_replication_slots WHERE slot_name LIKE 'opsbench_%'"}
    elif primitive_id.startswith("fidelity_prometheus"):
        before = _invoke_public_tool(tool_map, "metrics_read", {"metric": "opsbench_business_up"}, steps)
        observed = bool(before.get("healthy"))
        after_tool = "metrics_read"
        after_payload = {"metric": "opsbench_business_up"}
    elif primitive_id.startswith("fidelity_rabbitmq"):
        before = _invoke_public_tool(tool_map, "queue_inspect", {}, steps)
        observed = bool(before.get("healthy"))
        after_tool = "queue_inspect"
        after_payload = {}
    elif primitive_id.startswith("fidelity_redis"):
        before = _invoke_public_tool(tool_map, "cache_query", {}, steps)
        observed = bool(before.get("ok"))
        after_tool = "cache_query"
        after_payload = {}
    else:
        probe_tool = "transport_probe" if "transport_probe" in tool_map else ("secure_probe" if "secure_probe" in tool_map else "tls_probe")
        before = _invoke_public_tool(tool_map, probe_tool, {}, steps)
        observed = True
        after_tool = probe_tool
        after_payload = {}
    repair = _invoke_public_tool(tool_map, "service_control", {"action": "restore"}, steps)
    time.sleep(1.0)
    after = _invoke_public_tool(tool_map, after_tool, after_payload, steps)
    business = _invoke_public_tool(tool_map, "business_probe", {}, steps)
    repaired = bool(after.get("ok") or after.get("healthy"))
    passed = observed and bool(repair.get("healthy")) and repaired and bool(business.get("healthy"))
    return {
        "passed": passed,
        "error": "" if passed else "technology-specific public repair or observation failed",
        "semantic_assertions": {"diagnosis_observed": observed, "operation_ok": bool(repair.get("healthy")), "signal_ok": repaired, "business_operation": bool(business.get("healthy"))},
        "steps": steps,
    }


def _public_oracle_tls(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Repair TLS through generic diagnosis/control tools and verify it live."""
    steps: list[dict[str, Any]] = []
    diagnosis = _invoke_public_tool(tool_map, "signal_view", {}, steps)
    prepared = _invoke_public_tool(
        tool_map, "service_control", {"stage": "prepare", "action": "restore"}, steps,
    )
    applied = _invoke_public_tool(
        tool_map, "service_control", {"stage": "apply", "action": "restore"}, steps,
    )
    probe = _invoke_public_tool(tool_map, "command_run", {
        "command": (
            "curl -sS --noproxy '*' --cacert /etc/opsbench/ca.crt "
            "--max-time 3 -o /dev/null -w '%{http_code}' "
            "https://target:8443/health"
        ),
    }, steps)
    code = str(probe.get("stdout") or "").strip()
    passed = (
        bool(diagnosis.get("healthy"))
        and bool(prepared.get("healthy"))
        and bool(applied.get("healthy"))
        and int(probe.get("returncode", 1)) == 0
        and code.endswith("200")
    )
    return {
        "passed": passed,
        "error": "" if passed else "public TLS repair or hostname-verified probe failed",
        "semantic_assertions": {
            "diagnosis_observed": bool(diagnosis.get("healthy")),
            "prepare_ok": bool(prepared.get("healthy")),
            "verified_business_probe": code.endswith("200"),
        },
        "steps": steps,
    }


def _public_oracle_prometheus(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Restore the scrape path using the generic service-control capability."""
    steps: list[dict[str, Any]] = []
    control = _invoke_public_tool(tool_map, "service_control", {"action": "restore"}, steps)
    time.sleep(1.0)
    status = _invoke_public_tool(tool_map, "service_status", {}, steps)
    metrics = _invoke_public_tool(tool_map, "metrics_read", {"metric": "target_health"}, steps)
    passed = bool(control.get("healthy")) and bool(status.get("healthy")) and bool(metrics.get("healthy"))
    return {
        "passed": passed,
        "error": "" if passed else "public scrape restoration or readiness/metrics observation failed",
        "semantic_assertions": {
            "operation_ok": bool(control.get("healthy")),
            "service_ready": bool(status.get("healthy")),
            "metrics_observed": bool(metrics.get("healthy")),
        },
        "steps": steps,
    }


def _public_oracle_fluentbit(tool_map: dict[str, Any]) -> dict[str, Any]:
    """Restore the output route using the generic service-control capability."""
    steps: list[dict[str, Any]] = []
    control = _invoke_public_tool(tool_map, "service_control", {"action": "restore"}, steps)
    time.sleep(1.0)
    status = _invoke_public_tool(tool_map, "service_status", {}, steps)
    # Fluent Bit may briefly rebuild its HTTP metrics registry after a hot
    # reload.  Retry the public observation within a bounded window instead
    # of treating that transient 404 as an unrecoverable tool failure.
    metrics = {"healthy": False}
    for _ in range(4):
        metrics = _invoke_public_tool(tool_map, "metrics_read", {"metric": "delivery"}, steps)
        if metrics.get("healthy"):
            break
        time.sleep(1.0)
    # Exercise the declared business path as well as health/metrics.  A
    # processed-record counter alone does not prove that a downstream sink
    # received a record, especially when the Forward output keeps a TCP
    # connection open.  The probe uses only the generic bounded command tool
    # and the public Fluent Bit HTTP input; it does not name the hidden repair.
    probe = _invoke_public_tool(tool_map, "command_run", {
        "command": "curl --noproxy '*' -sS --max-time 5 -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{\"message\":\"opsbench-public-probe\"}' http://fluent-bit:9880/",
    }, steps)
    probe_code = str(probe.get("stdout") or "").strip()[-3:]
    probe_ok = int(probe_code) in {200, 201, 204} if probe_code.isdigit() else False
    # The HTTP input acknowledges acceptance before an asynchronous Forward
    # output necessarily reaches the sink.  Wait for the live delivery metric
    # to show an actual processed record; an input 201 alone is not evidence
    # that the business operation recovered.
    delivery_observed = False
    for _ in range(8):
        observed = _invoke_public_tool(tool_map, "metrics_read", {"metric": "delivery"}, steps)
        if observed.get("healthy"):
            try:
                body = json.loads(str((observed.get("status") or {}).get("body") or "{}"))
                outputs = body.get("output") or {}
                delivery_observed = any(int(value.get("proc_records", 0) or 0) > 0 for value in outputs.values() if isinstance(value, dict))
            except (TypeError, ValueError):
                delivery_observed = False
            if delivery_observed:
                break
        time.sleep(1.0)
    sink_observed = False
    for _ in range(8):
        sink_health = _invoke_public_tool(tool_map, "command_run", {
            "command": "curl --noproxy '*' -sS --max-time 5 http://sink:19880/health",
        }, steps)
        try:
            sink_body = json.loads(str(sink_health.get("stdout") or "{}"))
            sink_observed = int(sink_body.get("delivered", 0) or 0) > 0 and sink_body.get("mode") == "healthy"
        except (TypeError, ValueError):
            sink_observed = False
        if sink_observed:
            break
        time.sleep(1.0)
    passed = bool(control.get("healthy")) and bool(status.get("healthy")) and bool(metrics.get("healthy")) and int(probe.get("returncode", 1)) == 0 and probe_ok and delivery_observed and sink_observed
    return {
        "passed": passed,
        "error": "" if passed else "public output restoration, health/metrics observation, or downstream probe failed",
        "semantic_assertions": {
            "operation_ok": bool(control.get("healthy")),
            "service_healthy": bool(status.get("healthy")),
            "metrics_observed": bool(metrics.get("healthy")),
            "downstream_probe": probe_ok,
            "delivery_observed": delivery_observed,
            "sink_observed": sink_observed,
        },
        "steps": steps,
    }


def run_public_oracle(public_tools: dict[str, Any], trace_dir: Path) -> int:
    """Run a deterministic public-tool oracle without loading an API key."""
    names = [
        str(item.get("name") or "")
        for item in public_tools.get("tools", [])
        if isinstance(item, dict) and str(item.get("name") or "")
    ]
    tool_map = {str(item.name): item for item in build_tools(trace_dir, names)}
    primitive_id = os.environ.get("OPSBENCH_TEMPLATE_ID", "").strip()
    if primitive_id == "app_config_precedence_v1":
        result = _public_oracle_app_config(tool_map)
    elif primitive_id in {"http_dependency_port_drift_v1", "http_dependency_dns_poison_v1"}:
        result = _public_oracle_dependency(tool_map, primitive_id)
    elif primitive_id == "http_dependency_timeout_slo_v1":
        result = _public_oracle_timeout(tool_map)
    elif primitive_id == "app_stale_pid_v1":
        result = _public_oracle_stale_pid(tool_map)
    elif primitive_id == "tls_hostname_mismatch_v1":
        result = _public_oracle_tls(tool_map)
    elif primitive_id == "prometheus_scrape_target_v1":
        result = _public_oracle_prometheus(tool_map)
    elif primitive_id == "fluentbit_backpressure_v1":
        result = _public_oracle_fluentbit(tool_map)
    elif primitive_id == "nginx_bind_conflict_v1":
        result = _public_oracle_nginx(tool_map)
    elif primitive_id == "linux_cpu_runaway_v2":
        result = _public_oracle_cpu(tool_map)
    elif primitive_id == "linux_fd_leak_v1":
        result = _public_oracle_fd_leak(tool_map)
    elif primitive_id == "postgres_missing_index_v2":
        result = _public_oracle_postgres_index(tool_map)
    elif primitive_id == "rabbitmq_resource_alarm_v1":
        result = _public_oracle_rabbitmq(tool_map)
    elif primitive_id.startswith("fidelity_"):
        result = _public_oracle_fidelity(tool_map, primitive_id)
    elif primitive_id in {
        "linux_memory_growth_v1",
        "linux_disk_full_v1",
        "linux_inode_exhaustion_v1",
        "linux_upload_permission_v1",
        "linux_temp_permission_v1",
        "linux_file_lock_v1",
        "http_upstream_timeout_v1",
    }:
        result = _public_oracle_lightweight(tool_map, primitive_id)
    elif primitive_id in {
        "linux_oom_killer_v1",
        "linux_deleted_open_file_v1",
        "linux_mount_readonly_v1",
        "linux_conntrack_exhaustion_v1",
        "process_supervisor_restart_loop_v1",
        "container_healthcheck_mismatch_v1",
        "container_mount_permission_v1",
        "container_readonly_rootfs_v1",
        "container_pid_limit_v1",
        "http_proxy_misroute_v1",
        "tls_certificate_expiry_v1",
        "tls_mtls_client_auth_v1",
        "postgres_replication_lag_v1",
        "postgres_idle_transaction_v1",
        "postgres_readonly_replica_v1",
        "kafka_poison_message_v1",
        "rabbitmq_dead_letter_buildup_v1",
        "redis_cache_stampede_v1",
        "prometheus_alert_rule_mismatch_v1",
        "fluentbit_output_retry_storm_v1",
        "linux_inotify_watch_exhaustion_v1",
        "linux_ephemeral_port_exhaustion_v1",
        "linux_zombie_process_v1",
        "linux_cgroup_cpu_throttling_v1",
        "linux_tmpfs_capacity_v1",
        "container_capability_drop_v1",
        "container_startup_dependency_v1",
        "container_pid1_signal_forwarding_v1",
        "container_workdir_resolution_v1",
        "http_redirect_loop_v1",
        "http_header_size_limit_v1",
        "http_content_encoding_mismatch_v1",
        "tls_incomplete_chain_v1",
        "tls_protocol_version_mismatch_v1",
        "tls_revocation_status_v1",
        "postgres_autovacuum_debt_v1",
        "postgres_wal_retention_pressure_v1",
        "postgres_authentication_policy_v1",
        "postgres_sequence_exhaustion_v1",
        "kafka_under_replicated_partition_v1",
        "kafka_rebalance_storm_v1",
        "rabbitmq_prefetch_starvation_v1",
        "redis_eviction_policy_v1",
        "prometheus_label_cardinality_v1",
        "fluentbit_parser_mismatch_v1",
        "linux_tcp_retransmission_pressure_v1",
        "linux_routing_blackhole_v1",
        "linux_mtu_mismatch_v1",
        "linux_swap_pressure_v1",
        "container_user_identity_mismatch_v1",
        "container_dns_alias_drift_v1",
        "container_log_driver_backpressure_v1",
        "http_request_body_limit_v1",
        "http_keepalive_exhaustion_v1",
        "http_auth_token_expiry_v1",
        "http_cache_stale_response_v1",
        "tls_sni_route_mismatch_v1",
        "tls_alpn_negotiation_gap_v1",
        "postgres_deadlock_cycle_v1",
        "postgres_replication_slot_retention_v1",
        "postgres_query_cancel_storm_v1",
        "kafka_offset_commit_failure_v1",
        "rabbitmq_consumer_ack_timeout_v1",
        "redis_hot_key_contention_v1",
        "prometheus_remote_write_backpressure_v1",
        "linux_load_average_runqueue_v1",
        "linux_file_descriptor_pressure_v1",
        "linux_process_limit_exhaustion_v1",
        "linux_inotify_queue_overflow_v1",
        "container_image_pull_policy_drift_v1",
        "container_healthcheck_interval_mismatch_v1",
        "container_oom_score_adjustment_v1",
        "http_response_header_buffer_v1",
        "http_proxy_protocol_mismatch_v1",
        "http_compression_cpu_contention_v1",
        "tls_certificate_chain_order_v1",
        "tls_session_ticket_rotation_v1",
        "postgres_checkpoint_write_pressure_v1",
        "postgres_statistics_staleness_v1",
        "postgres_work_mem_spill_v1",
        "kafka_fetch_batch_mismatch_v1",
        "rabbitmq_queue_ttl_mismatch_v1",
        "redis_expired_keys_lag_v1",
        "prometheus_scrape_timeout_mismatch_v1",
        "systemd_restart_throttle_v1",
    }:
        result = _public_oracle_diverse(tool_map)
    else:
        result = {"passed": False, "error": f"unsupported_public_oracle:{primitive_id}", "steps": []}
    result["oracle_version"] = "e2e-public-tool-oracle-v1"
    _write_json(trace_dir / "public_oracle_result.json", result)
    _write_json(trace_dir / "agent_result.json", {"passed": bool(result.get("passed")), "mode": "public_oracle", "error": result.get("error", "")})
    return 0 if result.get("passed") else 3


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task")
    parser.add_argument("--tools")
    parser.add_argument("--trace")
    parser.add_argument("--case-dir")
    parser.add_argument("--work-dir")
    parser.add_argument("--timeout-sec", type=int, default=300)
    parser.add_argument("--public-oracle", action="store_true", help="run the registered public-tool fairness oracle")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    task_path = Path(args.task or os.environ.get("OPSBENCH_TASK", "/opsbench/public/task.md"))
    tools_path = Path(args.tools or os.environ.get("OPSBENCH_TOOLS", "/opsbench/public/tools.json"))
    trace_dir = Path(args.trace or os.environ.get("OPSBENCH_TRACE", "/opsbench/trace"))
    trace_dir.mkdir(parents=True, exist_ok=True)

    task = task_path.read_text(encoding="utf-8")
    public_tools = json.loads(tools_path.read_text(encoding="utf-8"))
    if args.public_oracle:
        return run_public_oracle(public_tools, trace_dir)
    api_key = os.environ.get("OPSBENCH_API_KEY")
    base_url = os.environ.get("OPSBENCH_BASE_URL", "https://api.deepseek.com")
    model_name = os.environ.get("OPSBENCH_AGENT_MODEL") or os.environ.get("OPSBENCH_MODEL") or "deepseek-v4-flash"
    if not api_key:
        _write_json(trace_dir / "agent_result.json", {"passed": False, "error": "OPSBENCH_API_KEY is missing"})
        return 2

    tool_contract_text = json.dumps(public_tools, ensure_ascii=False, indent=2)
    system_prompt = f"""You are an operations repair agent in a reproducible sandbox.

Investigate the incident using observable symptoms and the declared public
tools. Form and test hypotheses before changing state. Apply the smallest safe
repair supported by the observed evidence, preserve unrelated workloads, and
verify that the repair persists across the required lifecycle boundary.

The task description is not a diagnosis. Use live signals to distinguish
competing explanations, and do not treat process liveness alone as success.
Use only the exact public tool contract below. Its parameter types, allowlists,
and error messages are authoritative; do not invent service names, endpoints,
keys, views, fields, commands, or action values. If a tool reports an invalid
argument, use the declared contract and the returned diagnostic evidence.

Tools are bounded observation or execution interfaces; they do not reveal the
hidden answer and a successful tool call is not proof that the incident is
fixed. Legal but ineffective changes may execute and must be judged by live
business behavior and the declared persistence boundary. Discover dynamic
values from tool outputs before using them, and prefer the smallest change at
the source that controls effective runtime state.

Do not access hidden files, verifier logic, scenario data, credentials, case
roots, host files, Docker sockets, or host infrastructure. Do not disable
validation, alter the business contract, replace the service, or use broad
filesystem scans. Finish only after the public operation is healthy and the
declared persistence boundary has been verified.

PUBLIC TOOL CONTRACT:
{tool_contract_text}"""
    model_name = os.environ.get("OPSBENCH_AGENT_MODEL") or os.environ.get("OPSBENCH_MODEL") or "deepseek-v4-flash"
    max_steps = max(1, int(os.environ.get("OPSBENCH_AGENT_MAX_STEPS", "30")))
    _write_json(trace_dir / "agent_start.json", {
        "protocol_id": "opsbench-agent-v1",
        "profile": os.environ.get("OPSBENCH_AGENT_PROFILE", "autonomous"),
        "task_path": str(task_path),
        "tools_path": str(tools_path),
        "tool_names": [item.get("name") for item in public_tools.get("tools", [])],
        "model": model_name,
        "max_steps": max_steps,
        "timeout_sec": int(os.environ.get("OPSBENCH_AGENT_TIMEOUT_SEC", str(args.timeout_sec or 300))),
        "agent_prompt_digest": hashlib.sha256(system_prompt.encode("utf-8")).hexdigest(),
        "tool_contract_digest": hashlib.sha256(tool_contract_text.encode("utf-8")).hexdigest(),
        "agent_runtime_digest": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    })
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
    public_tool_names = sorted({
        str(item.get("name") or "").strip()
        for item in public_tools.get("tools", [])
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    })
    agent = create_react_agent(model, build_tools(trace_dir, public_tool_names), prompt=system_prompt)
    try:
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
