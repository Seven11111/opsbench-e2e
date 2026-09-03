# DeepSeek V4 Flash evaluation of the 106-case E2E pool

This release snapshot contains the 106 case packages from the validated
OpsBench E2E candidate pool together with the completed DeepSeek V4 Flash
evaluation.

## Contents

- `cases/`: 106 complete case packages, including public task/tool files and
  the private environment/evaluator needed for reproducibility.
- `results/manifest.json`: frozen evaluation inventory.
- `results/details.jsonl`: one persisted result record per case.
- `results/summary.json`: aggregate evaluation summary.
- `results/checkpoint.json`: final per-case checkpoint; `completed_count` is
  106 and `status` is `complete`.
- `provenance/`: source pool manifests used to assemble the case snapshot.

## Evaluation result

The configured `deepseek-v4-flash` agent completed 104 of 106 cases. The
overall task success rate was 75/106 (70.75%), with 29 model failures and 2
timeouts. There were no infrastructure errors and no Docker cleanup residue.
The average verifier score was 80.77%.

These results are an evaluation snapshot for expert review. They do not claim
empirical difficulty calibration or final benchmark selection.

The original factory paths are retained in the copied manifests and result
records as provenance; the case packages themselves are available under this
release directory for inspection.
