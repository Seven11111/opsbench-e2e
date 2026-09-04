# New 40-case Docker-gated release

This release contains the two fresh 20-case waves generated on 2026-09-03
and 2026-09-04. The second wave was generated from new official retrievals and
does not reuse the first wave's scenario provenance or case content.

- `cases/`: 40 complete E2E packages, including the public task/tools,
  evaluator, runtime environment, and lifecycle scripts.
- `provenance/candidates-v4.jsonl` and `provenance/candidates-v5.jsonl`:
  candidate provenance for the two waves.
- `provenance/documents-v4.jsonl` and `provenance/documents-v5.jsonl`:
  official evidence snapshots used by the two fresh generation runs.
- `results/runtime-controls-v4.json` and `results/runtime-controls-v5.json`:
  Docker runtime/control gate checkpoints.
- `results/generation-v4.json` and `results/generation-v5.json`:
  generation checkpoints.

Both waves completed static validation and the full Docker runtime/control
gate, including negative controls, repeatability, cleanup, and three public
oracle repetitions per case: 20/20 for each wave, 40/40 overall.

Every new case records `provenance_reused: false` and uses a distinct scenario
family. This release is an evaluable Docker-gated case collection; it does not
claim empirical difficulty calibration.
