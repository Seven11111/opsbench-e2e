# OpsBench E2E Demo Dataset

这是一个独立的 OpsBench 风格真实任务数据包，包含 3 个可以在 Docker 中真实执行和验证的 E2E case：Easy、Medium、Hard 各 1 个。

## 数据集概览

| 难度 | Case | 故障场景 | 主要能力 | 目标分数 |
|---|---|---|---|---:|
| Easy | `dynamic_nginx_bind_conflict_v1_000001` | Nginx 监听端口冲突 | 日志/端口诊断、服务恢复 | 3 |
| Medium | `dynamic_linux_cpu_runaway_v2_000003` | 受 supervisor 影响的 CPU runaway | 进程定位、CPU 采样、持久修复 | 5 |
| Hard | `dynamic_postgres_missing_index_v2_000001` | PostgreSQL 缺失索引导致查询计划退化 | SQL、EXPLAIN、索引设计、性能验证 | 9 |

目标分数使用 `e2e-difficulty-v1` 确定性 rubric：0–3 为 easy，4–6 为 medium，7–10 为 hard。当前三个 case 的 `empirical_status` 均为 `not_calibrated`，目标难度不是多模型通过率结论。

## 目录结构

```text
.
├── cases/
│   ├── dynamic_nginx_bind_conflict_v1_000001/
│   ├── dynamic_linux_cpu_runaway_v2_000003/
│   └── dynamic_postgres_missing_index_v2_000001/
├── agents/langchain-react-agent/
├── provenance/
│   ├── documents.jsonl
│   ├── annotations.jsonl
│   ├── bundles.jsonl
│   ├── scenario_specs.jsonl
│   ├── candidates.jsonl
│   ├── model_reviews.jsonl
│   └── revision_history.jsonl
├── results/
│   ├── e2e_manifest.json
│   ├── runtime_controls.json
│   ├── static_validation.json
│   ├── agent_summary.json
│   ├── agent_details.jsonl
│   ├── details.jsonl
│   ├── runs.jsonl
│   └── traces/
└── docs/
    ├── report_zh.md
    └── case_layout.md
```

每个 case 都包含：

- `manifest.yaml`：任务标签、故障类型、技术栈、难度和生命周期；
- `public/task.md`：Agent 可见的任务描述；
- `public/tools.json`：公开工具协议；
- `environment/docker-compose.yaml`：受限运行环境；
- `scripts/`：setup、inject、check-injected、cleanup；
- `evaluator/`：隐藏 scenario 和 verifier，不能被 Agent 读取。

## 运行环境

需要：

1. Docker Desktop / Docker Engine；
2. 当前 `opsbench-factory` 项目的 `opsbench` CLI；
3. 如果运行模型 Agent，需要设置 API 配置。

API Key 不在本仓库中。运行 Agent 前，在本地环境设置：

```powershell
$env:OPSBENCH_API_KEY = "<your-key>"
$env:OPSBENCH_BASE_URL = "<provider-base-url>"
$env:OPSBENCH_MODEL = "deepseek-v4-flash"
```

Case 只通过运行器获取模型配置；API Key 不传递给目标服务的 shell 工具，也不写入任务包或 trace。

## 静态验证

在本仓库根目录执行：

```powershell
opsbench validate-e2e --case-root cases
```

该命令验证 manifest、路径、公开/隐藏边界、Compose 配置、模板字段和 verifier 契约。

## 构建 E2E Manifest

```powershell
opsbench eval e2e-manifest `
  --case-root cases `
  --sample-size 3 `
  --sample-seed 42 `
  --output results/e2e_manifest.json
```

## 使用 ReAct Agent 评测

本数据包附带最小 `langchain-react-agent` 入口。Agent 使用统一协议读取公开任务和工具：

```text
--task <task.md> --tools <tools.json> --trace <trace-dir>
```

在 Docker container execution 模式下运行：

```powershell
opsbench eval e2e-run `
  --manifest results/e2e_manifest.json `
  --agent-command '["/agent/run.sh"]' `
  --execution-mode container `
  --output-dir results/agent-eval
```

结果包括：

- `summary.json`：整体成功率和分组统计；
- `details.jsonl`：每个 case 的 phase、verifier check、耗时和错误；
- `traces/`：Agent 启动记录、工具调用和执行 trace。

## 本次已验证结果

本次使用 `deepseek-v4-flash` ReAct Agent，每个 case 执行 1 次：

| Case | Agent 完成 | Verifier | 耗时 |
|---|---:|---:|---:|
| Nginx | 通过 | 通过 | 117.3 s |
| Linux CPU | 通过 | 通过 | 155.1 s |
| PostgreSQL | 通过 | 通过 | 44.6 s |
| **总计** | **3/3** | **3/3** | **平均 105.7 s** |

整体指标：`task_success_rate=1.0`、`execution_completion_rate=1.0`、`verifier_check_rate=1.0`、`timeout_rate=0`、`cleanup_failure_rate=0`。

每个 case 还完成了 baseline、injection、no-op、oracle、wrong-fix、partial-fix、restart-only、repeat 和 cleanup 控制；oracle 成功，负面控制按预期失败，最终没有残留容器、网络或 volume。

## 文档证据与生成状态

三个 case 的 provenance 来自官方文档：

- [Nginx listen directive](https://nginx.org/en/docs/http/ngx_http_core_module.html#listen)
- [Nginx command-line switches](https://nginx.org/en/docs/switches.html)
- [Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html)
- [Linux PSI](https://docs.kernel.org/next/accounting/psi.html)
- [PostgreSQL Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)
- [PostgreSQL Examining Index Usage](https://www.postgresql.org/docs/16/indexes-examine.html)

每个证据条目记录来源 URL、content hash、精确 span、claim type 和 excerpt hash，可从 `provenance/` 重算生成链路。

需要注意：本次本地 smoke run 中 DeepSeek 的题目生成请求超时，因此保留的候选在 `results/summary.json` 中标记为 `fallback_after_deepseek_timeout`，候选生成使用了确定性 fallback。运行评测阶段的 Agent 仍然真实使用 `deepseek-v4-flash`。因此，本仓库可以证明 case、Docker、verifier 和 Agent 协议可运行，但不能把本次结果当作 DeepSeek 题目生成质量实验。

## 汇报材料

- [中文汇报](docs/report_zh.md)
- [Case 目录、权限和生命周期](docs/case_layout.md)
- [统一 E2E Manifest](results/e2e_manifest.json)
- [Runtime Gate 结果](results/runtime_controls.json)
- [Agent 汇总结果](results/agent_summary.json)

## 许可证与使用说明

本仓库主要保存实验数据、Docker case 和运行记录。使用其中的官方文档内容时，请遵守对应来源网站的许可证和使用条款；本仓库不包含任何 API Key 或宿主机凭据。
