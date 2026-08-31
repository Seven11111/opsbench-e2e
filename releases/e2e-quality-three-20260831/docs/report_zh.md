# 三个高质量 E2E Case 汇报摘要

## 1. 本次目标

验证近期的质量优先流程是否能够稳定完成：

```text
已有清洗文档 → 证据选择 → 单候选生成 → Judge/修补 → trusted renderer
→ 静态校验 → Docker runtime gate → Agent 评测
```

本次不追求数量，也不把“hard”标签解释为已经校准的经验难度。

## 2. Case

| Case | 场景 | 目标难度 | 结果 |
|---|---|---:|---|
| `dynamic_app_config_precedence_v1_000001` | 高优先级配置覆盖预期服务状态 | hard | Agent 通过 |
| `candidate_http_dependency_timeout_slo_v1_001` | 依赖延迟导致业务请求超过 SLO | medium | Agent 通过 |
| `app_config_precedence_candidate_001` | 配置优先级造成服务不可达 | hard | Agent 通过 |

两个配置优先级 case 来自不同生成/证据运行，保留它们是为了检查同一能力的变体是否都能运行；它们不应被当成两个完全不同的运维场景。

## 3. 质量结果

- 3/3 case 静态校验通过；
- 3/3 case 通过 Docker runtime gate；
- 每个 case 的 baseline、故障注入、注入检查、正负控制、重复运行和 cleanup 均有记录；
- 0 个基础设施错误；
- 0 个超时；
- 0 个 cleanup failure；
- 3/3 Agent 评测完成并通过 verifier。

Runtime gate 的作用是确认题目确实可评测，包括 no-op、oracle 和错误/部分修复控制；它不是 Agent 成绩。

## 4. Agent 实验条件

| 项目 | 设置 |
|---|---|
| Agent | 容器内 LangChain ReAct-compatible runner |
| 模型 | `deepseek-v4-flash` |
| 步数 | 60 |
| temperature | 0 |
| Agent timeout | 600 秒 |
| 执行方式 | Docker target container |
| 重复次数 | 每题 1 次 |

汇总结果：

```text
task_success_rate = 100%
execution_completion_rate = 100%
conditional_success_rate = 100%
verifier_check_rate = 100%
average_duration = 67.74 s
```

“全部通过”只能说明当前 Flash 配置在这 3 个 smoke case 上完成了任务，不能证明题目简单或困难，也不能替代多次、多模型校准。

## 5. 可追溯材料

- `results/e2e_manifest.json`：冻结的 3 题评测清单；
- `results/flash-60-600/summary.json`：总体指标；
- `results/flash-60-600/details.jsonl`：逐题 phase、verifier check、耗时和 digest；
- `results/flash-60-600/traces/`：Agent metadata、工具调用和运行日志；
- `results/runtime-controls/`：每题 Docker runtime gate；
- `provenance/generation/`：输入文档、证据、候选、Judge 和 revision；
- `cases/`：可复现的完整 case package。

## 6. 结论和限制

这批结果证明当前生成的 3 个 case 在本机 Docker 和 Agent 协议下可评测，流程基本跑通。它还不能证明能力覆盖足够多，也不能证明 hard/medium 的经验难度已经建立。下一轮应优先增加不同能力和不同文档来源，并使用固定 Agent 配置多次重复，避免仅通过提高 timeout 把问题隐藏起来。
