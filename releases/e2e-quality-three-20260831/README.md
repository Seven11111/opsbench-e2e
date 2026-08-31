# Quality-first E2E smoke release (2026-08-31)

本 release 保存最近生成的 3 个 E2E case、生成 provenance、Docker runtime
gate 记录以及统一 Agent 评测结果。它是“质量优先”的 smoke release，不是
正式 benchmark，也不宣称已经完成经验难度校准。

## Case inventory

| Case | 场景 | 目标难度 | case status | Agent result |
|---|---|---:|---|---|
| `dynamic_app_config_precedence_v1_000001` | 配置优先级导致 HTTP 服务异常 | hard | evaluable | passed |
| `candidate_http_dependency_timeout_slo_v1_001` | HTTP 依赖延迟/超时导致 SLO 违约 | medium | evaluable | passed |
| `app_config_precedence_candidate_001` | 配置优先级导致 HTTP 服务不可达（变体） | hard | evaluable | passed |

本批 3 个 case 均通过静态校验和 runtime gate。需要注意：其中两个是同一
`app_config_precedence_v1` 能力的不同生成/证据变体，因此本批用于验证流程
和可评测性，不用于证明场景多样性。

## Generation and release checks

生成模型为 `deepseek-v4-flash`，审核模型为 `deepseek-v4-pro`，每次只生成
一个 candidate。流程为：

```text
existing cleaned documents
  -> evidence extraction and selection
  -> one ScenarioSpec
  -> source/evidence judge
  -> trusted renderer
  -> static validation
  -> Docker runtime gate
  -> evaluable case
```

本批使用了已有的清洗文档输入，保留在
`provenance/generation/*/input/documents.jsonl`；没有把 API key 或 `.env`
复制到 release。

## Runtime gate

每个 case 均完成了 baseline、setup、inject、check_injected、no-op、oracle、
负面控制、repeat 和 cleanup。控制运行次数分别为 9、10、9；三题的
`results/runtime-controls/` 中保存了完整控制汇总。runtime gate 的结论是：

```text
3/3 cases evaluable
runtime gate: passed
cleanup failures: 0
```

## Agent evaluation

三个 case 使用同一个容器内 LangChain ReAct-compatible Agent：

```text
model: deepseek-v4-flash
max_steps: 60
temperature: 0
agent timeout: 600 seconds
execution: Docker target container
protocol: opsbench-agent-v1
repeats: 1
```

结果：

```text
task_success_rate: 1.0000
execution_completion_rate: 1.0000
conditional_success_rate: 1.0000
verifier_check_rate: 1.0000
timeout_rate: 0.0000
infrastructure_error_rate: 0.0000
cleanup_failure_rate: 0.0000
average_duration_sec: 67.74
```

这是一次单次 Flash smoke run，不能据此判断难度；三个 case 的
`empirical_status` 仍为 `not_calibrated`。Agent trace 位于
`results/flash-60-600/traces/`，包含 Agent metadata、工具调用、标准输出和
verifier phase 记录。trace 中没有保存 API key。

## Reproduce locally

在 `opsbench-factory` 项目中、从本 release 目录执行：

```powershell
conda run -n opsdata python -m opsbench_factory.cli.main validate-e2e `
  --case-root cases

conda run -n opsdata python -m opsbench_factory.cli.main eval e2e-manifest `
  --case-root cases `
  --sample-size 3 `
  --sample-seed 42 `
  --output results/e2e_manifest.local.json

conda run -n opsdata python -m opsbench_factory.cli.main eval e2e-run `
  --manifest results/e2e_manifest.local.json `
  --agent-config configs/flash-60-600.yaml `
  --output-dir results/local-run `
  --execution-mode container `
  --repeats 1
```

评测时需要在本机环境提供 API key 和 provider base URL；仓库不包含任何密钥：

```powershell
$env:OPSBENCH_API_KEY = "<your-key>"
$env:OPSBENCH_BASE_URL = "<provider-base-url>"
```

## Directory layout

```text
cases/                         完整本地 case package（含 hidden verifier）
configs/flash-60-600.yaml      可复现实验配置，不含密钥
provenance/generation/         文档、证据、候选、Judge 和 revision 记录
results/e2e_manifest.json      frozen evaluation inventory
results/flash-60-600/          Agent summary、details 和 traces
results/runtime-controls/      每个 case 的 Docker runtime gate
dataset_manifest.json          release inventory 和 digest
docs/report_zh.md               中文汇报摘要
```

`cases` 是供专家审阅和本地复现的完整快照；如果作为公开测试集发布，需另行
只暴露 `public/`，将 `evaluator/`、`scripts/` 和内部 scenario 保留在服务端。
