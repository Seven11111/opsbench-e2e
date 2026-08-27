# Repaired Hard E2E Cases: PostgreSQL and Redis

This release records the repair and re-evaluation of two manually authored
hard E2E cases from `opsbench-factory`:

| Case | Domain | Target difficulty | Final GLM result |
|---|---|---:|---:|
| `postgres-recurring-lock-hard-v2-001` | PostgreSQL/database | hard, score 10 | pass |
| `redis-refresh-drift-hard-v2-001` | Redis/cache | hard, score 10 | pass |

The cases are complete runnable packages under `cases/private/`. They are
intended for expert diagnosis of case design, tool protocol, runtime controls,
and difficulty—not as a claim that the benchmark is already calibrated.

## What was repaired

The original packages had an invalid non-canonical task label,
`safe_remediation`, and had lifecycle/runtime issues. The repaired snapshot:

- uses canonical labels `fault_fix`, `fault_detection`, and `root_cause`;
- adds trusted runtime controls for both custom template IDs;
- removes stale worker PID files after process termination;
- terminates orphan PostgreSQL lock sessions during oracle/verifier cleanup;
- mounts `last-sync.json` and `last-refresh.json` so the verifier can observe
  real lifecycle progress;
- adds bounded waits and subprocess error checking to setup, injection, and
  injected-state checks;
- passes the public tool contract, including exact enum values, into the
  packaged ReAct Agent prompt to prevent blind parameter guessing.

## Reproduce

From the `opsbench-factory` source project, with Docker Desktop running:

```powershell
opsbench validate-e2e `
  --case-root releases/e2e-hard-two-v2-repaired-20260827/cases/private

opsbench eval e2e-manifest `
  --case-root releases/e2e-hard-two-v2-repaired-20260827/cases/private `
  --sample-size 2 `
  --sample-seed 42 `
  --output releases/e2e-hard-two-v2-repaired-20260827/results/e2e_manifest.json

opsbench eval e2e-run `
  --manifest releases/e2e-hard-two-v2-repaired-20260827/results/e2e_manifest.json `
  --agent-config releases/e2e-hard-two-v2-repaired-20260827/agents/e2e-glm-60.yaml `
  --output-dir releases/e2e-hard-two-v2-repaired-20260827/results/glm-rerun
```

The repository does not contain an API key. Set the provider credentials only
in the local environment before running an Agent.

## Evidence and limitations

The Docker runtime gate passed for both cases: 7/7 controls per case,
including oracle, negative controls, repeat, and cleanup. The final GLM result
was 2/2. However, the case manifests still contain empty `source.evidence_refs`
and a placeholder-style `dynamic_bundle_0001`; the original source documents
are not bundled here. Therefore this snapshot is runtime-validated but not
provenance-complete. Both cases also remain `runtime_status: experimental` and
`empirical_status: not_calibrated`.

See [`docs/diagnosis_zh.md`](docs/diagnosis_zh.md) for the full timeline and
the questions prepared for expert review.
