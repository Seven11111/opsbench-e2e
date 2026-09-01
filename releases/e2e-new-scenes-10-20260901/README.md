# E2E New Scenes 10-case Release

本 release 保存 2026-09-01 完成的一批新场景 E2E case，供专家复核和本地复现实验使用。它不是已经完成 Agent panel 难度校准的正式 benchmark；`target_difficulty` 表示结构化设计目标，`empirical_status` 仍为 `not_calibrated`。

## Case inventory

| Case | Primitive | Domain | Target difficulty | Flash result |
|---|---|---|---|---|
| `01-file-lock` | `linux_file_lock_v1` | linux | medium | failed |
| `05-tls-hostname` | `tls_hostname_mismatch_v1` | tls | hard | failed |
| `15-prometheus-scrape` | `prometheus_scrape_target_v1` | observability | medium | failed |
| `16-fluentbit-backpressure` | `fluentbit_backpressure_v1` | logging | hard | failed |
| `19-memory-growth` | `linux_memory_growth_v1` | linux | medium | failed |
| `23-upstream-timeout` | `http_upstream_timeout_v1` | network | medium | failed |
| `24-stale-pid` | `app_stale_pid_v1` | configuration | medium | passed |
| `25-config-precedence` | `app_config_precedence_v1` | configuration | hard | passed |
| `27-upload-chmod` | `linux_upload_permission_v1` | linux | easy | failed |
| `28-temp-tmpfiles` | `linux_temp_permission_v1` | linux | easy | failed |

## Generation and quality gates

The batch used the following flow:

```text
new official documents
  -> crawl/clean and provenance
  -> evidence selection and Source Judge
  -> one ScenarioSpec per candidate
  -> trusted renderer
  -> static task/tool/verifier alignment
  -> Docker runtime gate
  -> unified Agent evaluation
```

There were 36 input job attempts. Ten cases were frozen after generation and selection. All ten passed static validation and the complete Docker runtime gate, including baseline, injection, no-op, oracle, negative controls, repeat, and cleanup. No case was included because of a model result alone.

## Agent evaluation

All cases used exactly the same configuration:

```text
model: deepseek-v4-flash
max_steps: 60
temperature: 0
agent timeout: 600 seconds
protocol: opsbench-agent-v1
execution: Docker
repeats: 1
```

Results:

```text
evaluable cases: 10
agent completed: 10
passed: 2
failed: 8
execution completion rate: 1.0000
task success rate: 0.2000
timeouts: 0
infrastructure errors: 0
cleanup failures: 0
average duration: 140.4484 seconds
```

The eight failures were recorded after the Agent completed and the verifier returned failure (`task_failure`). They were not API timeout or Docker infrastructure failures. Inspect `results/details.jsonl` and the corresponding directory under `results/traces/` before using any failure as evidence of model capability.

## Reproduce locally

From this release directory, with the project dependencies installed:

```powershell
conda run -n opsdata python -m opsbench_factory.cli.main validate-e2e --case-root cases
conda run -n opsdata python -m opsbench_factory.cli.main eval e2e-manifest --case-root cases --sample-size 10 --sample-seed 42 --output results/e2e_manifest.local.json
conda run -n opsdata python -m opsbench_factory.cli.main eval e2e-run --manifest results/e2e_manifest.local.json --agent-config agents/flash-60-600.yaml --output-dir results/reproduce
```

The repository does not contain an API key or `.env` file. Reproduction requires the user to configure the model provider in the local environment.

## Directory layout

```text
cases/                       complete local case packages, including hidden evaluator files
agents/flash-60-600.yaml     frozen Agent configuration
results/e2e_manifest.json    frozen ten-case inventory
results/details.jsonl        per-case Agent and verifier results
results/summary.json         aggregate metrics
results/traces/              Agent and runtime traces
results/runtime-controls/    per-job Docker quality-gate reports
provenance/generation/       documents, evidence, candidates, Judge and revision records
reports/smoke_report_zh.md   Chinese generation/evaluation report
reports/smoke_summary.json   machine-readable attempt and selection summary
```

This is a full internal review package. For public benchmark distribution, publish only the public task/tool portions and keep `evaluator/`, lifecycle scripts, private scenario data, and runtime-control implementations on the evaluation side.
