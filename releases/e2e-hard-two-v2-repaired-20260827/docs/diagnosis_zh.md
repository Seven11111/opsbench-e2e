# 本次修复与评测诊断报告

## 1. 结论

两个 case 现在都可以通过静态校验、Docker runtime gate 和 GLM Agent
评测。最终按 case 汇总为 2/2 成功，但这只能说明当前 case 可执行、当前
Agent 在当前配置下能够解决，不能单独证明它们具有已校准的 hard 难度。

## 2. 原始问题

### 静态问题

两个 manifest 曾使用 `safe_remediation`，但它不是项目 taxonomy 中的
canonical task label，因此初次静态校验失败。修复为：

```text
primary_task_label: fault_fix
secondary_task_labels: [fault_detection, root_cause]
```

### 运行时问题

第一次 Docker 检查中发现：

1. setup/inject 没有严格检查目标容器命令的返回码；
2. worker 被杀掉后 PID 文件残留，supervisor 会误判 worker 仍存活；
3. PostgreSQL worker 的子进程可能留下孤儿 advisory-lock 会话；
4. `last-sync.json` 和 `last-refresh.json` 没有挂载回宿主机，verifier 无法
   观察最近的真实周期；
5. 注入后的即时检查存在 supervisor 重启竞争，需要有限重试；
6. 自定义 template ID 没有 runtime-control 注册项，不能安全地沿用通用
   status-file 控制。

### Agent 问题

首轮 GLM 评测不是 Docker/API 失败。Agent 大量猜测不存在的服务名、视图、
endpoint 和配置键，例如 PostgreSQL 猜测未声明的 `pg_stat_activity` 视图，
Redis 猜测未声明的服务和 key，最后两个 case 都没有成功。

原因是 `tools.json` 中的枚举约束没有进入嵌入式 ReAct Agent 的模型上下文；
工具实现虽然会拒绝非法参数，但模型看不到完整 allowlist。

## 3. 修复内容

- 修复 case 副本中的 taxonomy 标签；
- 在 `src/opsbench_factory/e2e/controls.py` 增加：
  `postgres_recurring_lock_chain_v2` 和
  `redis_refresh_contract_drift_v2` 的可信控制注册；
- setup/inject/check/cleanup 增加返回码检查、超时和有限等待；
- worker 停止后删除 PID 文件；
- PostgreSQL oracle/verifier 按 `application_name=inventory-sync` 终止
  孤儿数据库会话；
- Compose 显式挂载两个生命周期状态文件；
- Agent system prompt 注入完整公开工具契约，并要求严格遵守枚举；
- 通用 `agents/langchain-react-agent/run.py` 同步增加该工具契约提示。

原始目录 `tmp/e2e-hard-two-v2` 未修改；本 release 使用的是
`tmp/e2e-hard-two-v2-repaired` 的修复副本。

## 4. Docker runtime gate

每个 case 执行 7 次：

```text
no_op
oracle
restart_only
wrong_fix
partial_fix
repeat #1
repeat #2
```

“负控 verifier 返回 false”是预期行为；runtime gate 将其解释为负面控制
正确拒绝，而不是把错误修复判成成功。

结果：

| Case | 控制运行 | Oracle | 负控行为 | Cleanup |
|---|---:|---|---|---|
| PostgreSQL recurring lock | 7/7 | 通过 | 全部按预期失败 | 通过 |
| Redis refresh drift | 7/7 | 通过 | 全部按预期失败 | 通过 |

## 5. GLM 评测过程

评测配置为 `glm-4.7`、60 steps、temperature 0、Docker target container。

### 首轮

```text
PostgreSQL: fail
Redis: fail
task_success_rate: 0/2
原因：Agent 盲猜工具参数，未进入可靠修复流程
```

### 第二轮：加入完整 tools.json 契约

```text
PostgreSQL: pass
Redis: timeout
```

PostgreSQL trace 显示 Agent 能够读取 activity、locks、blocking graph，比较
base/effective configuration，清理环境覆盖，并完成持久修复。

### 第三轮：补充 Redis 的公开操作流程

Redis Agent 按以下路径完成：

```text
读取 catalog:active 和 catalog:meta
→ 检查 TTL
→ 比较 base/effective schema_version
→ 删除 refresh.env 中的 schema_version 覆盖
→ 触发 refresh
→ 验证 catalog、TTL、preview 和 worker
```

最终 Redis 结果：

```text
task_success_rate: 1.0
execution_completion_rate: 1.0
conditional_success_rate: 1.0
verifier_check_rate: 1.0
timeout_rate: 0.0
cleanup_failure_rate: 0.0
verifier_score: 1.0
```

最终按 case 取最新有效结果：

```text
PostgreSQL: pass, verifier score 1.0, duration 260.468 sec
Redis:      pass, verifier score 1.0, duration 111.313 sec
```

## 6. 对“难度是否有效”的判断

当前困难机制是有效的结构化设计，但尚未完成经验校准。

有效部分包括：

- 多配置层和 effective state；
- supervisor/refresh worker 带来的故障复现；
- 直接重启、直接改当前值等短路方案不能持久解决；
- PostgreSQL 需要区分 reporting session 和 causal lock；
- Redis 需要保留 TTL、preview key 和刷新机制。

仍然偏容易的部分包括：

- 正确的配置键在公开工具中可直接读取；
- 两个 case 的最终修复路径较集中；
- 当前只对 GLM 做了少量单次评测；
- 结构化 difficulty score=10 是规则分，不是经验难度。

因此建议标记为：

```text
target_difficulty: hard
empirical_status: not_calibrated
runtime_status: experimental/runtime-validated
```

## 7. provenance 限制

本 release 的 case manifest 中：

```text
source.evidence_refs: []
source.evidence_bundle_id: dynamic_bundle_0001
```

这意味着本次修复和评测证明了运行可靠性，但没有证明这两个 case 已经由
可复核的真实文档证据驱动生成。专家如果要评审“文档驱动生成质量”，还需要
补充原始文档、精确 span、content hash、EvidenceBundle 和生成记录。

## 8. 建议专家重点回答的问题

1. 两个故障机制是否足够接近真实生产事故，而不是人为构造的状态机？
2. `reporting session`、`preview key` 等干扰项是否合理，还是增加了不必要
   的提示噪声？
3. 公开工具是否泄漏了过多根因信息？
4. 当前 hard 机制是否应增加更多可信观测信号和更长的持久化边界？
5. 两个 case 的公开修复路径是否过于集中？
6. verifier 是否覆盖了真正的业务目标，而不是只检查配置文件？
7. 文档 provenance 应采用哪些最小字段和专家审核标准？
8. 后续 Agent panel 应使用哪些弱/强配置，才能证明难度区分度？
