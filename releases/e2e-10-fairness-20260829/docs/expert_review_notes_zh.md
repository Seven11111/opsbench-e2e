# 专家诊断说明

## 1. 本批次目的

本批次用于验证修改后的 E2E 生成链路能否连续工作：

```text
参考文档/已审核证据
  -> 单候选 ScenarioSpec
  -> Source Judge（最多 3 轮）
  -> trusted renderer
  -> 静态校验
  -> Docker runtime gate
  -> evaluable
  -> Flash Agent 评测
```

本批使用 `artifact_mode=trusted`，因此 Docker Compose、生命周期脚本和
verifier 来自已注册的可信能力，而不是让模型自由编写。这样可以把“文档
驱动生成质量”和“模型生成运行时工件质量”分开观察。

## 2. 结果解释

所有 10 个入选 case 均通过了静态检查和 Docker runtime gate，说明它们可以
被正式 Agent runner 执行。Flash Agent 在同一配置下通过 5 个：

```text
task_success_rate          5/10 = 50.00%
execution_completion_rate  7/10 = 70.00%
conditional_success_rate   5/7  = 71.43%
timeout                    3/10 = 30.00%
infrastructure_error       0
cleanup_failure             0
```

`verifier_failed` 表示 Agent 已结束，但实际状态没有满足 verifier；它是模型
任务失败，不是环境不可评测。`agent_timeout` 表示 Agent 在 180 秒内没有完成，
应单独分析工具摩擦、诊断路径长度和问题难度，不能直接当作正常答错。

## 3. 需要重点诊断的问题

### 3.1 TLS 重复

两个 TLS 包的 `case_digest` 相同，说明当前 seed 或 renderer 组合没有带来真实
结构变化。建议在正式 benchmark 构建前增加 digest/fingerprint 去重门禁，要求
故障参数、可观测信号、工具集合或验证条件至少一项真实不同。

### 3.2 Nginx/TLS 超时

两类题目均是可运行的，但 Flash 没有在时间限制内完成。需要检查：

- 公共工具是否提供了足够的证据观察能力；
- 工具名称是否关联功能但没有泄漏答案；
- Agent 是否被迫进行过多重复探测；
- 180 秒是否适合这类任务；
- timeout 后 verifier 结果是否仅用于诊断，而不是被误归类为普通错误。

### 3.3 HTTP timeout/SLO

两道 HTTP timeout case 的 Agent 都完成了执行，但 verifier 分别发现
`latency_slo`、`dependency_delay` 或 `persistence` 未满足。这是有价值的正常
失败样本，但需要确认题面公开的 SLO 与 verifier 的阈值一致，不能让 Agent 只能
通过猜测隐藏阈值完成任务。

### 3.4 任务数量与独立性

当前 release 有 10 个包条目，但只有 9 个独立 digest。App 配置和 PostgreSQL
变体可以用于流程回归，但不应在论文中直接解释为 10 个完全独立的故障机制。

## 4. 证据和可追溯性

`provenance/source/` 保存本批使用的完整文档输入；
`provenance/generation/<case>/` 保存对应 run 的 input、evidence、Judge、
revision、runtime gate 和 manifest。EvidenceBundle 是来源索引，不是题目状态：
它记录文档 URL、content hash、精确 span、claim role 以及未使用文档。

本批曾出现的证据门禁拒绝也保存在 `provenance/rejections/`。其中包括：

- 多文档互补证据没有正确合并；
- 标题、FAQ 或参数说明被误作根因/修复证据；
- 公共工具描述泄漏注册故障词；
- 文档无法同时提供具体 root cause 和 repair span。

这些拒绝结果不进入 frozen manifest，但可用于改进后续生成和 Judge。

## 5. 对后续 benchmark 的建议

1. 先删除或替换重复 TLS 包，再形成正式候选集。
2. 对 timeout 题目增加工具调用上限和重复探测抑制，避免把协议摩擦误当难度。
3. 对 HTTP 题目补充公开但非答案唯一的 SLO/健康观察接口。
4. 对每个能力至少生成多个真实参数变体，并使用结构化 fingerprint 去重。
5. 对每题重复运行 3 次后再确定经验难度；本批 `empirical_status` 仍为
   `not_calibrated`。
6. trusted renderer 稳定后，再单独开启 staged-model，测试模型生成 Docker、
   生命周期脚本和 verifier 的能力，不与本批成绩混合。

## 6. 复核入口

- `results/e2e_manifest.json`：冻结的 10 题清单
- `results/flash_summary.json`：聚合指标
- `results/flash_details.jsonl`：逐题结果和 verifier checks
- `results/traces/`：Agent message/tool-call trace
- `provenance/rejections/`：失败候选及门禁原因
