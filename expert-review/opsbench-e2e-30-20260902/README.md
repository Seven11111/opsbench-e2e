# OpsBench E2E expert-review bundle

This submission contains exactly **30 newly generated E2E cases** for expert review.
The original six cases already present in the release pool are intentionally excluded.

Each case directory is a self-contained review package with its manifest, Docker
environment, evaluator, public task/tools, and setup/injection/check/cleanup scripts.
The cases were selected from the project's validated release pool after the Docker
runtime gate, repeat/control checks, and cleanup checks passed. Public-tool oracle
results are included when the staging report recorded them; legacy records without
that field are represented as `null` rather than inferred.

## Contents

- `cases/` — the 30 case packages
- `inventory.json` — IDs, primitives, digests, source runs, and gate summaries
- `provenance/` — the two staging runs' runtime-control reports and checkpoints

## Cases

- `candidate_http_dependency_timeout_001` — `http_dependency_timeout_slo_v1`
- `candidate_linux_disk_full_v1_001` — `linux_disk_full_v1`
- `candidate_linux_inode_exhaustion_001` — `linux_inode_exhaustion_v1`
- `candidate_postgres_missing_index_v2_001` — `postgres_missing_index_v2`
- `candidate_rabbitmq_resource_alarm_v1_001` — `rabbitmq_resource_alarm_v1`
- `candidate_redis_cache_corruption_001` — `redis_cache_corruption_v1`
- `candidate_tls_hostname_mismatch_v1_001` — `tls_hostname_mismatch_v1`
- `dynamic_app_config_precedence_v1_000001` — `app_config_precedence_v1`
- `dynamic_app_config_precedence_v1_000002` — `app_config_precedence_v1`
- `dynamic_app_config_precedence_v1_031002` — `app_config_precedence_v1`
- `dynamic_app_stale_pid_v1_000001` — `app_stale_pid_v1`
- `dynamic_app_stale_pid_v1_031003` — `app_stale_pid_v1`
- `dynamic_http_dependency_dns_poison_v1_031015` — `http_dependency_dns_poison_v1`
- `dynamic_http_dependency_port_drift_v1_031005` — `http_dependency_port_drift_v1`
- `dynamic_http_dependency_timeout_slo_v1_031006` — `http_dependency_timeout_slo_v1`
- `dynamic_http_retry_circuit_breaker_v1_000001` — `http_retry_circuit_breaker_v1`
- `dynamic_http_retry_circuit_breaker_v1_031012` — `http_retry_circuit_breaker_v1`
- `dynamic_kafka_consumer_lag_v1_000001` — `kafka_consumer_lag_v1`
- `dynamic_kafka_consumer_lag_v1_031008` — `kafka_consumer_lag_v1`
- `dynamic_linux_cpu_runaway_v2_000001` — `linux_cpu_runaway_v2`
- `dynamic_linux_cpu_runaway_v2_031009` — `linux_cpu_runaway_v2`
- `dynamic_linux_fd_leak_v1_000001` — `linux_fd_leak_v1`
- `dynamic_linux_fd_leak_v1_031010` — `linux_fd_leak_v1`
- `dynamic_linux_temp_permission_v1_000001` — `linux_temp_permission_v1`
- `dynamic_nginx_bind_conflict_v1_000001` — `nginx_bind_conflict_v1`
- `dynamic_postgres_connection_pool_exhaustion_v1_000001` — `postgres_connection_pool_exhaustion_v1`
- `dynamic_postgres_lock_contention_v1_000001` — `postgres_lock_contention_v1`
- `dynamic_tls_hostname_mismatch_v1_031011` — `tls_hostname_mismatch_v1`
- `http_dependency_dns_poison_v1_candidate_1` — `http_dependency_dns_poison_v1`
- `http_dependency_port_drift_v1_candidate_001` — `http_dependency_port_drift_v1`

The full staging paths and gate metadata are retained in `inventory.json` and the
reports under `provenance/`; raw agent traces are not included in this review bundle.
