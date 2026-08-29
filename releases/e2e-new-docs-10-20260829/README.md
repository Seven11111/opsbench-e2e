# New-document E2E smoke report

Date: 2026-08-29

This report records the selected ten cases generated from fresh official-document inputs. The
selected manifest is `results/e2e_manifest.json`; older `*-v2`, `*-v3`, `*-final`, and similar
directories in this run are intermediate attempts and are not part of the selected ten-case set.

## Generation and release gate

The selected cases followed:

```text
new document input -> clean/evidence provenance -> single ScenarioSpec
-> model review and repair -> trusted case renderer -> static validation
-> Docker runtime controls -> evaluable case -> Agent evaluation
```

- Candidate policy: one candidate and one case per scenario.
- Model review: the selected runs contain one to three review records; failed reviews were
  returned to the generator before the case was accepted.
- Runtime controls: baseline, injection, injected-state check, no-op, oracle, wrong-fix,
  partial-fix, restart-only, repeat, and cleanup.
- All ten selected package manifests report `case_status: evaluable` and
  `runtime_gate_passed: true`.
- Static validation passed for all ten selected case packages.
- Docker endpoint used for this run: Docker Desktop Linux Engine through the explicit named pipe
  endpoint. No host path or Docker socket was exposed to the Agent.

## Selected cases

| Case | Scenario | Source document | Target difficulty | Runtime | Flash result |
|---|---|---|---|---|---|
| `dynamic_http_retry_circuit_breaker_v1_000001` | HTTP retry/circuit-breaker recovery | [Azure Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker) | hard (8) | evaluable | failed: task failure |
| `dynamic_kafka_consumer_lag_v1_000001` | Kafka consumer lag recovery | [Kafka consumer configuration](https://kafka.apache.org/41/configuration/consumer-configs) | hard (8) | evaluable | passed |
| `dynamic_linux_disk_full_v1_000001` | Linux disk exhaustion recovery | [GNU `df` invocation](https://www.gnu.org/software/coreutils/manual/html_node/df-invocation.html) | medium (5) | evaluable | passed |
| `dynamic_linux_file_lock_v1_000001` | Linux file-lock recovery | [Python `fcntl`](https://docs.python.org/3/library/fcntl.html) | medium (5) | evaluable | failed: task failure |
| `dynamic_linux_inode_exhaustion_v1_000001` | Linux inode exhaustion recovery | [GNU `df` invocation](https://www.gnu.org/software/coreutils/manual/html_node/df-invocation.html) | medium (5) | evaluable | passed |
| `dynamic_linux_memory_growth_v1_000001` | Linux memory-growth recovery | [Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html) | medium (5) | evaluable | failed: task failure |
| `dynamic_linux_upload_permission_v1_000001` | Linux upload permission recovery | [Python `os` interface](https://docs.python.org/3/library/os.html) | easy (3) | evaluable | failed: task failure |
| `dynamic_postgres_connection_pool_exhaustion_v1_000001` | PostgreSQL connection-pool recovery | [PgBouncer usage](https://www.pgbouncer.org/usage) | hard (8) | evaluable | failed: task failure |
| `dynamic_postgres_lock_contention_v1_000001` | PostgreSQL lock-contention recovery | [PostgreSQL explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html) | hard (8) | evaluable | failed: task failure |
| `dynamic_redis_cache_corruption_v1_000001` | Redis cache-corruption recovery | [Redis cache-aside pattern](https://redis.io/docs/latest/develop/use-cases/cache-aside/) | hard (8) | evaluable | failed: task failure |

The target difficulty is a structural label, not an empirically calibrated difficulty claim. All
ten cases remain `empirical_status: not_calibrated`.

## Flash evaluation

Configuration: `configs/e2e-flash-60.yaml`, model `deepseek-v4-flash`, 60 steps, one run per case,
container execution. The model prompt and public tool contract were shared by all ten cases.

The first full pass exposed one runner-side Docker image-reference error for the Kafka case. The
runner was corrected to generate strictly alphanumeric case components in Compose project names;
Kafka was then rerun in isolation. The corrected result below replaces the original infrastructure
error and is the result included in the final aggregate.

| Metric | Result |
|---|---:|
| Cases | 10 |
| Evaluable | 10 |
| Agent completed | 10 |
| Passed | 3 |
| Normal verifier/task failures | 7 |
| Infrastructure errors | 0 |
| Timeouts | 0 |
| Cleanup failures | 0 |
| Task success rate | 30.0% |
| Conditional success rate | 30.0% |
| Average duration | 113.892 s |

The seven failed runs completed the Agent protocol and reached the verifier; they are normal task
failures, not API or Docker failures. The failed verifier checks are retained in `details.jsonl`.
In particular, a failed check means that the Agent did not establish the full required repaired
state, persistence, or business condition for that case. It does not mean that the case is
unevaluable.

## Artifact locations

- `results/e2e_manifest.json`: frozen ten-case manifest and case digests.
- `results/flash/details.jsonl`: one detailed result per selected case.
- `results/flash/summary.json`: corrected aggregate summary.
- `results/flash/traces/`: Agent traces referenced by the detailed results.
- Each selected scenario run contains `evidence/`, `candidates/`, `reviews/`, `revisions/`,
  `provenance/`, `cases/`, and `reports/runtime_controls.json`.

The exact source spans and content hashes remain in each selected run's evidence and provenance
artifacts. The source document is used to ground the scenario and public facts; a document does not
need to be repeated in every field or all of its text to be considered a valid source.

## Interpretation

This is a successful generation and runtime-evaluation smoke batch: all ten generated packages are
structurally valid and executable, and three of ten were solved by the current Flash Agent in one
run. It is not yet a claim that the hard/medium/easy labels are calibrated, nor a final benchmark
release. Repeated runs and an Agent panel are still needed before using these ten cases as evidence
for model ranking or difficulty separation.
