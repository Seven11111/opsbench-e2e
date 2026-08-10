# Easy / Medium / Hard E2E Demo 汇报

## 结论

本次发布包含 3 个由官方文档提供证据、可在 Docker 中真实运行的 E2E case：

| 难度 | 场景 | Primitive | 运行门禁 |
|---|---|---|---|
| Easy | Nginx 端口占用导致服务启动失败 | `nginx_bind_conflict_v1` | 通过 |
| Medium | Linux 后台任务持续 CPU runaway | `linux_cpu_runaway_v2` | 通过 |
| Hard | PostgreSQL 缺失索引导致查询退化 | `postgres_missing_index_v2` | 通过 |

## 数据来源与生成链路

每个 case 使用 2 篇官方文档，经过 crawl、clean、label 和精确 evidence span 整理，形成可追溯的 EvidenceBundle。随后生成 3 个候选，执行证据、任务和执行一致性审核，最多允许 3 轮定向修补，最后由可信 renderer 编译为 OpsBench 风格 case package。

本地 DeepSeek 生成请求在本次 smoke run 中超时，因此本次发布的候选生成使用了项目内置的确定性 fallback，并在 manifest 中记录为 `generator_model=heuristic_fallback`。这证明了文档证据、候选结构、可信编译器和 Docker 运行链路可用，但不应把本次结果解释为 DeepSeek 生成质量实验。生成器和审核器仍保留 `deepseek-v4-flash`、`deepseek-v4-pro` 以及最多 3 轮 Judge 反馈配置，后续可在 API 通道稳定后重新生成。

## Runtime Gate

三个 case 均完成 baseline、injection、no-op、oracle、wrong-fix、partial-fix、restart-only、repeat 和 cleanup 控制。Nginx 使用真实 HTTP 和进程状态验证；CPU case 使用容器 CPU 采样、进程状态和服务健康验证；PostgreSQL 使用真实查询结果、`EXPLAIN (FORMAT JSON)`、索引状态和查询延迟验证，不依赖 `status.json`。

三组 runtime controls 全部通过，cleanup failure 为 0，且未发现残留容器、网络或 volume。

## ReAct Agent Smoke Test

使用当前 `langchain-react-agent` 和 `opsbench-agent-v1` 协议对三个 case 各执行 1 次：

- 完成率：3/3
- verifier 通过率：3/3
- 平均耗时：约 105.7 秒
- cleanup failure：0

详细结果见 `results/agent_summary.json`、`results/agent_details.jsonl` 和 `results/traces/`。这次单次运行用于证明 Agent 协议、容器边界和 verifier 可用，不用于证明难度校准。

## 难度说明

难度是确定性 rubric 下的目标设计难度，当前尚未通过多模型 Agent panel 校准：

- Easy：3 分，目标区间 0–3
- Medium：5 分，目标区间 4–6
- Hard：9 分，目标区间 7–10

三个 case 的 `empirical_status` 均为 `not_calibrated`，primitive 状态为 `demo_validated`，不会仅凭本次 3 个 case 宣称已完成正式难度校准。

## 复现材料

- `cases/`：三个可运行 case package
- `provenance/`：文档、证据、bundle、候选、审核和修补记录
- `results/e2e_manifest.json`：统一评测 manifest
- `results/runtime_controls.json`：运行门禁结果
- `results/agent_summary.json`：ReAct Agent 汇总结果
- `docs/case_layout.md`：case 目录和权限边界说明
