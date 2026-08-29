# E2E Expert-Fairness Smoke Release

This release contains three newly generated, document-driven E2E cases from
`opsbench-factory`. The cases were generated as one candidate per document
bundle, passed the source/Judge checks, passed static package validation, and
passed the Docker runtime gate before Agent evaluation.

## Cases

| Package | Primitive | Source | Target difficulty | Judge score | Runtime |
|---|---|---|---|---:|---|
| `linux-stale-pid-medium-001` | `app_stale_pid_v1` | systemd.service | medium / 5 | 4.87 | passed |
| `http-upstream-timeout-medium-001` | `http_upstream_timeout_v1` | NGINX proxy module | medium / 5 | 4.54 | passed |
| `docker-compose-config-precedence-hard-001` | `app_config_precedence_v1` | Docker Compose environment precedence | hard / 8 | 4.94 | passed |

## Generation pipeline

```text
official document URL
  -> HTTP-only crawl and full cleaned context
  -> evidence extraction and strict evidence gate
  -> one ScenarioSpec candidate
  -> source/task/execution Judge (up to 3 rounds)
  -> trusted renderer
  -> static task/tool/verifier fairness checks
  -> Docker runtime controls
  -> evaluable case package
```

The TLS hostname candidate generated during the same experiment was rejected
by the strict Judge because the model cited unrelated SSL blocking and SSL 3.0
passages. It is intentionally not included in this release.

## Runtime gate

Each included case completed baseline, injection, injection verification,
no-op, oracle, wrong-fix, partial-fix, restart-only, repeat, and cleanup
controls. The per-case control reports are included under
`results/runtime-controls/`.

## Agent evaluation

The three cases were evaluated with the configured DeepSeek Flash60 ReAct
agent through the Alibaba Bailian-compatible endpoint. The evaluation used
the same 60-step agent configuration and container execution mode for all
cases. Results are recorded as:

```text
case_status: evaluable = 3
execution_status: completed = 3
model_result: passed = 0, failed = 3
timeout: 0
infrastructure_error: 0
cleanup_failure: 0
```

The failures are verifier failures after completed agent runs, not Docker or
API failures:

- stale PID: business health, root-signal removal, and persistence were not
  achieved;
- upstream timeout: the 503/timeout condition remained active;
- config precedence: business behavior and effective state recovered, but the
  repair did not persist across the lifecycle boundary.

This smoke release demonstrates evaluability and failure attribution. It does
not claim empirical difficulty calibration from one Agent run per case.

## Repository contents

- `cases/`: complete local case packages, including hidden evaluator files;
- `provenance/`: source documents, evidence bundles, and generation manifests;
- `results/e2e_manifest.json`: frozen evaluation inventory;
- `results/flash-60/summary.json`: aggregate Agent result;
- `results/flash-60/details.jsonl`: per-case Agent and verifier results;
- `results/runtime-controls/`: per-case Docker control reports;
- `dataset_manifest.json`: portable inventory and source summary.

No `.env`, API key, Docker socket, or host credential is included.
