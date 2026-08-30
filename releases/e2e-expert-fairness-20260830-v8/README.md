# Expert fairness repair: three E2E cases

This release contains the three repaired case packages from the expert-fairness
round completed on 2026-08-30. The packages are copied from the frozen local
run `expert-fairness-3-repaired-20260830-v8` and are intended for inspection,
reproduction, and later agent evaluation.

## Contents

| Case | Scenario | Runtime status | Case status |
|---|---|---|---|
| `repaired_app_config_precedence_v1_001` | Configuration precedence and durable application recovery | `demo_validated` | `evaluable` |
| `repaired_http_dependency_timeout_slo_v1_001` | HTTP dependency timeout and SLO recovery | `demo_validated` | `evaluable` |
| `repaired_app_stale_pid_v1_001` | Stale process state and service recovery | `demo_validated` | `evaluable` |

Each case includes the OpsBench-style package: `manifest.yaml`, public task
and tool contract, Compose environment, lifecycle scripts, and hidden
evaluator files. The public task is the agent input; `scenario.json`,
`inject.py`, and `evaluator/verify.py` are private evaluator material.

## Runtime validation

The frozen Docker runtime gate reported `passed=true` for all 3 cases across
26 control runs. For each case, the public oracle passed in 3 repeated runs.
The negative controls were expected to fail and did fail: no-op, restart-only,
wrong-layer or wrong-fix, partial-fix, and symptom-bypass where applicable.
The two repeat runs and cleanup passed for every case.

The exact machine-readable records are in:

- `results/runtime_controls.json`
- `results/generation_manifest.json`
- `results/reports/static_validation.jsonl`
- `results/summary.json`

The generation and provenance artifacts are in `generation/`, `reviews/`, and
`provenance/`. Raw Docker control traces remain in the local frozen run and
are intentionally not copied into this repository because they contain local
workspace paths and are not required to reproduce the case package.

## Important interpretation

`case_status=evaluable` means that the package and verifier passed the static
and runtime quality gate. It does not mean that an agent has solved the task.
Agent results must be produced with a separately frozen model, prompt, tool
contract, step budget, and timeout, and should not be mixed with this runtime
gate result.

The cases remain `demo_validated`; three runtime-valid cases are not enough to
claim capability calibration or empirical difficulty calibration.

## Reproduction

Run the repository's E2E validator against the three directories under
`cases/`, then use the repository runner with the complete case package and a
frozen agent configuration. The private evaluator must stay outside the
agent-visible task and tool files.
