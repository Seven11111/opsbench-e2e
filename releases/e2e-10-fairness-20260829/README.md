# E2E 10-case generation and evaluation snapshot

This release is a reproducible engineering snapshot from `opsbench-factory`,
not a claim of a fully calibrated benchmark. It contains ten case-package
entries generated with the single-candidate pipeline and evaluated with the
same DeepSeek Flash60 Agent configuration.

## What was run

```text
full cleaned document / reviewed evidence
  -> one ScenarioSpec candidate
  -> source Judge (up to three rounds)
  -> trusted renderer
  -> static validation
  -> Docker runtime gate
  -> evaluable case
  -> Flash60 Agent evaluation
```

Generation used `artifact_mode=trusted`: Docker, lifecycle scripts and the
verifier came from registered trusted renderers. The model generated the
scenario-level content, while the runtime gate independently checked that the
case was executable. The generation and review models were configured as
`deepseek-v4-flash` and `deepseek-v4-pro`, respectively, with no deterministic
fallback for this batch.

All ten selected packages passed static validation and the Docker runtime gate,
so all ten have `case_status=evaluable`. The Agent experiment used:

```yaml
model: deepseek-v4-flash
max_steps: 60
timeout_sec: 180
temperature: 0
repeats: 1
```

## Case inventory

| Release case | Primitive | Target difficulty | Runtime | Agent result |
|---|---|---:|---|---|
| `app-config-001` | `app_config_precedence_v1` | hard | evaluable | passed |
| `app-config-002` | `app_config_precedence_v1` | hard | evaluable | passed |
| `app-config-003` | `app_config_precedence_v1` | hard | evaluable | passed |
| `postgres-index-001` | `postgres_missing_index_v2` | hard | evaluable | passed |
| `postgres-index-002` | `postgres_missing_index_v2` | hard | evaluable | passed |
| `http-timeout-001` | `http_dependency_timeout_slo_v1` | medium | evaluable | failed |
| `http-timeout-002` | `http_dependency_timeout_slo_v1` | medium | evaluable | failed |
| `nginx-bind-001` | `nginx_bind_conflict_v1` | easy | evaluable | failed (timeout) |
| `tls-hostname-001` | `tls_hostname_mismatch_v1` | hard | evaluable | failed (timeout) |
| `tls-hostname-002` | `tls_hostname_mismatch_v1` | hard | evaluable | failed (timeout) |

The release contains ten package entries but only nine unique case digests:
the two TLS entries are byte-for-byte identical according to the frozen case
digest. They are retained so the expert can inspect the duplicate-generation
problem; they should not be counted as two independent benchmark instances.

## Flash evaluation

| Metric | Result |
|---|---:|
| cases | 10 |
| task success | 5/10 (50.0%) |
| execution completion | 7/10 (70.0%) |
| conditional success | 5/7 (71.43%) |
| verifier check rate | 59.46% |
| Agent timeout | 3/10 |
| infrastructure error | 0 |
| cleanup failure | 0 |
| average duration | 98.72 s |

Normal task failures were separated from Agent timeouts. The two normal
verifier failures were HTTP timeout/SLO cases: the Agent finished, but the
latency, dependency-delay or persistence checks were not all satisfied. The
three timeout results were Nginx/TLS runs. They are not infrastructure errors,
but they should be investigated before claiming calibrated difficulty.

## Directory layout

```text
cases/                         ten complete case packages
configs/e2e-flash-60.yaml      frozen Agent configuration
provenance/source/             selected full source documents
provenance/generation/         per-run input, evidence, Judge and gate data
provenance/rejections/         rejected generation attempts and reasons
results/e2e_manifest.json      repository-relative frozen manifest
results/flash_summary.json     sanitized evaluation summary
results/flash_details.jsonl    one record per Agent run
results/traces/                Agent messages and tool-call traces
results/batch_summary.json     release-level summary
```

## Reproduce static validation

From this release directory, with the `opsbench-factory` environment active:

```powershell
opsbench validate-e2e --case-root cases
```

The complete package is intentionally included for expert diagnosis. The
`evaluator/`, `scenario.json`, injection and cleanup files are hidden from the
Agent at runtime by the case runner; they are present here only so a reviewer
can inspect and reproduce the verifier behavior.

No API key is stored in this release. To rerun the Agent, configure the key in
the local environment and use the repository-relative manifest:

```powershell
opsbench eval e2e-run `
  --manifest results/e2e_manifest.json `
  --agent-config configs/e2e-flash-60.yaml `
  --output-dir results/flash-rerun `
  --repeats 1
```

## Review questions for experts

1. Are the public task and public tools sufficiently informative without
   exposing the root cause or the repair layer?
2. Do the negative controls distinguish a durable repair from a restart,
   symptom bypass or partial repair?
3. Are the timeout-heavy TLS/Nginx results caused by reasonable task
   difficulty, or by tool/protocol friction?
4. Should the duplicate TLS digest be rejected earlier by structural
   deduplication?
5. Which document-grounded variants should be added next to increase scenario
   diversity without relying on text-only rewrites?

The target difficulty labels in this snapshot are structural labels only;
`empirical_status` remains `not_calibrated`.
