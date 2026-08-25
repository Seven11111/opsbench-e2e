# OpsBench E2E Benchmark Pilot v0.2

Release status: `pilot_incomplete`

This release contains 11 statically valid E2E case packages selected from the
current runtime-capable case pool. The formal target is 48 cases, so this
release must not be described as the final paper benchmark.

## Inventory

```text
http_wrong_port_v1       4
linux_cpu_runaway_v1     4
linux_cpu_runaway_v2     1
nginx_bind_conflict_v1   1
postgres_missing_index_v2 1
```

The difficulty distribution is 1 easy, 9 medium, and 1 hard. The legacy
variants are not empirically difficulty-calibrated.

## Case layout

- `cases/private/`: complete local packages, including hidden scenario and
  verifier material;
- `cases/public/`: public task/tool projections;
- `dataset_manifest.json`: inventory, quotas, and provenance status;
- `provenance/cases.jsonl`: source and digest records;
- `results/e2e_manifest.json`: frozen local evaluation manifest;
- `results/runtime_status.json`: validation status for this pilot;
- `docs/benchmark_protocol.md`: evaluation protocol;
- `docs/paper_report_zh.md`: Chinese report notes.

## Validation status

All 11 packages passed static package validation. Three corresponding demo
cases have passed the complete Docker runtime control suite (baseline,
injection, negative controls, oracle, repeat, and cleanup). The other eight
cases are marked `runtime_pending`; they should not be used to claim a 100%
runtime release rate until their individual gates are run.

The current package is intended for reproducible development and protocol
testing. It does not provide balanced coverage across all registered
capabilities, and it does not establish empirical easy/medium/hard separation.

## Local commands

From the `opsbench-factory` project:

```powershell
opsbench validate-e2e --case-root releases/e2e-pilot-v0.2/cases/private
opsbench eval e2e-manifest `
  --case-root releases/e2e-pilot-v0.2/cases/private `
  --sample-size 11 `
  --sample-seed 42 `
  --output releases/e2e-pilot-v0.2/results/e2e_manifest.json
```

The private projection is included for local reproducibility. Because it
contains the verifier, it is not a blind public test set.
