# Expert-reviewed E2E case fixes

This release contains six E2E case packages repaired after expert review on
2026-09-01. The packages are copied from the local
`e2e-expert-review-20260901` validation run and are intended for inspection,
regression testing, and local model evaluation.

## Included cases

| Case directory | Scenario | Status |
|---|---|---|
| `01-file-lock` | Persistent file-lock failure | `evaluable` |
| `15-prometheus-scrape` | Prometheus file-SD target failure | `evaluable` |
| `16-fluentbit-backpressure` | Fluent Bit buffering/backpressure | `evaluable` |
| `19-memory-growth` | Persistent memory-growth failure | `evaluable` |
| `23-upstream-timeout` | Upstream timeout and recovery | `evaluable` |
| `27-upload-chmod` | Upload-directory permission failure | `evaluable` |

Each case keeps the OpsBench-style package layout with its manifest, public
task and tools, environment, lifecycle scripts, and evaluator. Runtime
generated `__pycache__` files are intentionally omitted.

## Validation

The source validation run recorded in
`reports/expert_fix_summary.json` reports:

- all six repaired cases passed the container runtime controls;
- each case completed eight control runs, including no-op, oracle, negative
  controls, repeat, and cleanup;
- no case-container residue remained after cleanup;
- the related E2E regression suite passed 53 tests.

The report is evidence from the local validation run, not a claim that these
cases have been calibrated across a model panel.

## Local use

Run the project's E2E static validator against the `cases` directory, then
use the repository's E2E runner with the case package and an agent command.
The evaluator and scenario files are included because this repository is an
internal review archive; an external benchmark release should publish only
the intended public package and keep hidden evaluator assets private.
