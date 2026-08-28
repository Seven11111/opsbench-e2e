# 生成、审核、发布和评测记录

## 1. 输入与来源

本次没有把所有历史文档混在一起，而是分别使用两个已有的、完整保存的 EvidenceBundle：

| case | 参考来源 | EvidenceBundle |
|---|---|---|
| app configuration precedence | Docker Compose environment variables 文档 | `provenance/app-config-precedence/evidence/bundles/` |
| HTTP dependency timeout / SLO | NGINX HTTP proxy module 文档 | `provenance/http-timeout-slo/evidence/bundles/` |

每个 bundle 保存：canonical/source URL、content hash、原文中的 evidence span、claim type、候选引用和 active/excluded 文档信息。文档不要求全部出现在题面；只要候选使用的公开事实可以回溯到来源即可。

## 2. 候选生成

本次配置是动态模式、单候选：

```text
generation_mode=dynamic
artifact_mode=trusted
group_size=1
generator=deepseek-v4-flash
reviewer=deepseek-v4-pro
max_judge_rounds=3
```

每个 EvidenceBundle 只生成一个 ScenarioSpec，不生成 A/B/C 题目。ScenarioSpec 随后被渲染为一个 case package。候选、ScenarioSpec、输入文档上下文和 manifest 分别在 `provenance/*/candidates/`、`provenance/*/input/` 和 `provenance/*/generation_manifest.json` 中保存。

模型生成的是场景语义、公开任务、合法工具集合和证据引用。由于本次使用 trusted artifact mode，Compose、setup/inject/check/cleanup 和 verifier 来自已注册 primitive 的 renderer，不由模型自由编写。这是为了先隔离验证文档驱动生成与运行时可靠性。

## 3. Source Judge

审核模型检查来源支持、任务清晰度、根因泄漏、可执行性和 verifier 对齐。失败时会保留结构化反馈并带回下一轮上下文，而不是静默丢弃：

```text
summary
observed_problem
likely_causes
required_changes
forbidden_changes
affected_fields
acceptance_conditions
```

App case 在第 1 轮通过，评分 4.84/5。

HTTP case 第 1 轮因为证据引用与生成的根因字段不匹配而失败，反馈中包含：

```text
REPAIR_EVIDENCE_MISMATCH
ROOT_CAUSE_EVIDENCE_IRRELEVANT
```

生成模型根据反馈修正引用/场景，第 2 轮通过，评分 4.74/5。完整记录见 `provenance/http-timeout-slo/reviews/model_reviews.jsonl` 和 `revisions/`。

## 4. 静态校验与发布状态

编译后分别检查：

```text
case schema 和 manifest
公开/隐藏路径边界
Compose 与资源限制
工具协议
verifier 输出结构
根因/修复信息是否泄漏到公开题面
```

两个 case 都通过静态校验，并且没有进入 `rejects/`。注意：静态通过并不等于 Agent 能完成任务；它只说明 case 结构可以进入运行时验证。

## 5. Docker runtime gate

两个 case 都完成了以下生命周期：

```text
validate
provision
setup
baseline_check
inject
check_injected
run_agent
verify
cleanup
```

runtime gate 内部确认基线健康、故障真实注入、Verifier 能识别状态和清理没有失败。完整原始报告在：

```text
results/runtime-gate/app-config-precedence.json
results/runtime-gate/http-timeout-slo.json
```

所以两个 case 的最终 `case_status` 都是 `evaluable`。

## 6. Flash Agent 评测

两题使用完全相同的 LangChain ReAct Agent 入口和 `flash_60`：

```text
model=deepseek-v4-flash
max_steps=60
temperature=0
agent_timeout_sec=180
```

每题本次运行一次，结果不是难度校准，只是协议与任务可解性的 smoke test。

### App configuration precedence

```text
agent_completed: true
case_status: evaluable
model_result: failed
failure_type: task_failure
score: 0.666667
duration_sec: 71.203
```

Verifier 结果：

| Check | 结果 |
|---|---|
| `business_operation` | passed |
| `effective_state` | passed |
| `reconciler_persistence` | failed |

Agent 修改后即时状态恢复，但没有完成能经受 reconciler 再次覆盖的持久修复。这是题目目标的一部分，属于正常答错；不是模型连接失败、Docker 启动失败或 verifier 崩溃。

### HTTP dependency timeout / SLO

```text
agent_completed: true
case_status: evaluable
model_result: passed
score: 1.0
duration_sec: 67.141
```

Verifier 结果：

| Check | 结果 |
|---|---|
| `business_operation` | passed |
| `latency_slo` | passed |
| `dependency_delay` | passed |
| `persistence` | passed |

## 7. Trace 与复核入口

每个 Agent run 下包含：

```text
agent_start.json
agent_messages.jsonl
tool_calls.jsonl
agent_result.json
baseline_probe.jsonl
public/task.md
public/tools.json
agent.stdout.log
agent.stderr.log
```

其中 `trace/tool_calls.jsonl` 可以回答“Agent 看到了什么、调用了什么工具、工具返回了什么”；`results/flash/*/details.jsonl` 可以回答“最终 verifier 哪个 check 通过或失败”。

## 8. 结论边界

本次可以确认：

1. 新生成的两个动态 case 经过了生成、Source Judge、可信编译、静态校验和 Docker runtime gate。
2. 两个 case 都可评测；一个 Agent 通过，一个 Agent 在持久性要求上正常失败。
3. HTTP case 展示了 Judge 失败反馈 → 生成模型修复 → 下一轮通过的完整记录。

本次不能确认：

1. hard/medium 已经完成经验难度校准；每个 case 只运行了一个模型配置和一次。
2. 两个 case 已代表完整 benchmark 分布。
3. Agent 失败一定来自题目难度；这里只能确认该次失败发生在最终 verifier 的持久性检查。

