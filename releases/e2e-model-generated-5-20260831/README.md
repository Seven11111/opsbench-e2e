# Model-generated E2E cases: 2026-08-30/31

This release records five model-generated, Docker-runnable E2E cases and the
DeepSeek Pro evaluation results. It is an experimental snapshot for review,
not a calibrated benchmark release.

## Contents

```text
cases/
  candidate_postgres_lock_contention_001/
  candidate_redis_cache_corruption_001/
  dynamic_http_retry_circuit_breaker_v1_000001/
  dynamic_kafka_consumer_lag_v1_000001/
  dynamic_postgres_connection_pool_exhaustion_v1_000001/
results/
  pro-60-180/       # original five-case run, 180 s Agent timeout
  pro-60-600/       # rerun of the three original timeouts, 600 s timeout
configs/
  pro-60-180.yaml
  pro-60-600.yaml
```

The case packages include the public task and tools, Compose environment,
lifecycle scripts, hidden scenario, and verifier used by the local runner.
No API key or `.env` file is included.

## Case inventory

| Case | Domain | Fault | Target difficulty | Runtime status |
|---|---|---|---|---|
| `candidate_postgres_lock_contention_001` | database | PostgreSQL lock contention | hard | evaluable |
| `candidate_redis_cache_corruption_001` | cache | Redis cache corruption | hard | evaluable |
| `dynamic_http_retry_circuit_breaker_v1_000001` | distributed system | HTTP retry/circuit breaker | hard | evaluable |
| `dynamic_kafka_consumer_lag_v1_000001` | messaging | Kafka consumer lag | hard | evaluable |
| `dynamic_postgres_connection_pool_exhaustion_v1_000001` | database | PostgreSQL connection pool exhaustion | hard | evaluable |

`hard` is the deterministic target design label. The cases are marked
`not_calibrated`; one or two model runs do not establish empirical difficulty.

## Evaluation protocol

The Agent was the repository's LangChain ReAct-compatible runner, executed in
the target container with the public task and public tools only. The evaluator
used:

```text
model: deepseek-v4-pro
max_steps: 60
temperature: 0
execution: Docker container
protocol: opsbench-agent-v1
```

The original run used a 180-second Agent wall-clock timeout. The three cases
that timed out were then rerun with the same model and Agent configuration,
changing only the timeout to 600 seconds. The rerun is a retry of those three
cases, not three additional dataset cases.

Each result records the separation between:

```text
case_status       evaluable / not_evaluable
execution_status  completed / timeout / infrastructure_error
model_result      passed / failed / not_scored
```

An Agent timeout is not automatically a model failure. A verifier failure after
the Agent completes is recorded as `model_result=failed`.

## Results: original 180-second run

Source: `results/pro-60-180/summary.json` and `details.jsonl`.

| Case | Result | Duration | Failed checks / reason |
|---|---|---:|---|
| PostgreSQL lock contention | `failed` | 194.2 s | `persistence` |
| Redis cache corruption | `not_scored` | 192.0 s | Agent timeout |
| HTTP retry/circuit breaker | `not_scored` | 192.7 s | Agent timeout |
| Kafka consumer lag | `passed` | 152.1 s | none |
| PostgreSQL connection pool | `not_scored` | 211.8 s | Agent timeout |

Summary:

```text
passed: 1/5
completed: 2/5
not_scored: 3/5
execution timeouts: 3
infrastructure errors: 0
cleanup failures: 0
```

## Results: 600-second rerun

Source: `results/pro-60-600/summary.json` and `details.jsonl`.

| Case | Agent phase | Total duration | Result | Verifier outcome |
|---|---:|---:|---|---|
| Redis cache corruption | 140.8 s | 155.7 s | `passed` | all checks passed |
| HTTP retry/circuit breaker | 217.8 s | 233.2 s | `failed` | service remained in failed/open state |
| PostgreSQL connection pool | 176.5 s | 196.3 s | `failed` | `persistence` failed |

Summary:

```text
passed: 1/3
completed: 3/3
not_scored: 0
execution timeouts: 0
infrastructure errors: 0
cleanup failures: 0
```

The 600-second rerun shows that the original three 180-second outcomes were
at least partly caused by an insufficient wall-clock budget. It does not turn
the two verifier failures into successes: they completed and were assessed as
failed by the verifier. The PostgreSQL pool case should receive a separate
task/verifier contract review because its business and holder checks passed
while its persistence check did not.

## Reproducibility

Run from the `opsbench-factory` project with Docker Desktop available. The
paths below are relative to this release directory after copying it into a
working case root.

```powershell
opsbench validate-e2e --case-root cases
opsbench eval e2e-manifest `
  --case-root cases `
  --sample-size 5 `
  --sample-seed 42 `
  --output results/e2e_manifest.json
opsbench eval e2e-run `
  --manifest results/e2e_manifest.json `
  --agent-config configs/pro-60-180.yaml `
  --output-dir results/local-run `
  --execution-mode container `
  --repeats 1
```

The frozen manifests, per-case details, phase records, verifier checks, and
traces in this release are the authoritative records for the two experiments.
The 180-second and 600-second summaries must not be concatenated into one
five- or eight-case success rate: the latter is a retry of three cases under a
different timeout condition.

## Interpretation

These results demonstrate that all five packages passed the static/runtime
case gate and that the container Agent protocol works. They also show why
timeout, infrastructure failure, and normal task failure must remain separate
diagnostic categories. The snapshot should be used to inspect task/tool/
verifier alignment before promoting any case to a formal benchmark.
