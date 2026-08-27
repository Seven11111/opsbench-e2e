# E2E Hard Pilot - 2026-08-27

This release is a review snapshot of five document-grounded E2E task packages
from `opsbench-factory`. It is intended for expert review of task design,
generation workflow, verifier design, and difficulty calibration.

This is not a calibrated benchmark release. All five packages are marked
`experimental` and `not_calibrated`.

## Inventory

| Case | Scenario | Static validation | Docker runtime gate | GLM-4.7 |
|---|---|---:|---:|---:|
| `postgres-lock-contention-hard-001` | PostgreSQL lock contention | pass | pass | pass |
| `postgres-connection-pool-hard-001` | PostgreSQL connection-pool exhaustion | pass | pass | pass |
| `redis-cache-corruption-hard-001` | Redis cache payload corruption | pass | pass | pass |
| `kafka-consumer-lag-hard-001` | Kafka consumer lag | pass | blocked | not evaluated |
| `http-retry-circuit-breaker-hard-001` | HTTP retry/circuit-breaker dependency drift | pass | pass | pass |

All five cases have deterministic structural difficulty `hard`, score `8/10`.
This is a design label, not an empirical model difficulty claim.

## Scenario summary

- PostgreSQL lock contention: a live blocking database session makes the orders
  endpoint fail while process and database health checks remain green.
- PostgreSQL connection-pool exhaustion: long-running sessions consume database
  capacity while PostgreSQL remains reachable.
- Redis cache corruption: Redis is healthy but the application-level payload
  contract is invalid and must be rebuilt without deleting the key.
- Kafka consumer lag: the broker is healthy but consumer progress is unstable;
  this package is quarantined because the consumer group remains in rebalancing.
- HTTP retry/circuit breaker: the caller is healthy but the effective downstream
  route is wrong and must be restored durably.

## Package layout

Each package under `cases/private` contains `manifest.yaml`, public task/tools,
Compose and Dockerfile files, runtime configuration, setup/injection/check/
cleanup scripts, and hidden scenario/verifier files. The private projection is
included for reproducibility and expert inspection; it must not be given to an
agent as an external blind test package.

## Generation and validation

The pipeline is:

`documents -> evidence provenance -> EvidenceBundle -> ScenarioSpec -> trusted
primitive renderer -> static validation -> Docker provision -> baseline/setup/
inject/check -> ReAct Agent -> live verifier -> cleanup -> runtime_validated or
quarantine`.

The current pilot uses registered trusted renderers and deterministic candidate
review. The generation model is not allowed to invent arbitrary images, host
mounts, Docker sockets, or verifier shortcuts.

Detailed explanations are in `docs/generation-flow.md`,
`docs/difficulty-design.md`, and `docs/expert-review-questions.md`.

## GLM evaluation

The Agent is the packaged LangChain/LangGraph ReAct implementation under
`agents/langchain-react-agent`. It was run with `glm-4.7`, 60 steps, temperature
0, and a 300-second per-agent timeout. The four runtime-ready cases all passed:

- task success rate: 1.00;
- execution completion rate: 1.00;
- timeout rate: 0.00;
- infrastructure error rate: 0.00;
- cleanup failure rate: 0.00;
- average duration: 75.12 seconds.

These results show that the execution protocol is usable. They do not establish
hard empirical difficulty because the tested GLM configuration solved every
runtime-ready case. Full details and traces are under `results/glm-4.7`.

## Local execution

Use the source project's `opsbench` CLI and a running Docker Desktop. No API key
is stored in this repository. Configure `OPSBENCH_API_KEY` only in the local
environment, then run `validate-e2e`, `eval e2e-manifest`, and `eval e2e-run` on
the private case directory. Never commit `.env`, tokens, private certificates,
or host credentials.

## Release status

The four runtime-ready cases are suitable as a runtime pilot and regression set.
They should not yet be described as a balanced or calibrated hard benchmark.
Before a formal release, fix the Kafka consumer-group lifecycle, normalize the
PostgreSQL/Redis verifier score weights, add genuine structural variants, and
run a repeated Agent panel.
