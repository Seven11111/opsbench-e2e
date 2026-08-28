# E2E Bailian Tool-Policy Smoke Release

本目录保存 2026-08-28 生成并执行的两个 E2E case，供专家复核生成流程、公开工具契约、运行时验证和 Agent 失败原因。

## 内容概览

| Case | 能力 | 参考文档 | case_status | Agent 结果 |
|---|---|---|---|---|
| `app-config-precedence-v1` | `app_config_precedence_v1` | [Docker Compose environment variable interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/) | `evaluable` | `failed` |
| `http-dependency-timeout-v1` | `http_dependency_timeout_slo_v1` | [NGINX proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) | `evaluable` | `failed` |

两个 case 都通过了静态校验、Compose 启动、故障注入、runtime controls 和 cleanup。Agent 进程也正常结束；`failed` 表示最终 verifier 发现任务没有修复完成，不表示 API、Docker 或 Runner 崩溃。

## 目录说明

```text
cases/
  app-config-precedence-v1/       完整 case package，含 public、environment、scripts、evaluator
  http-dependency-timeout-v1/    完整 case package
agents/langchain-react-agent/     本次使用的 LangChain ReAct Agent 入口副本
configs/                          本次评测配置摘要
provenance/
  app-config/                     文档、证据、候选、Judge、修补和生成 manifest
  http-timeout/                   同上
results/
  app-config/                     Agent 评测明细和完整 trace
  http-timeout/                   Agent 评测明细和完整 trace
  runtime-controls/               两个 case 的 baseline/injection/negative-control/repeat 结果
  report.json                     去除本机绝对路径后的汇总
```

## Case 1：配置优先级

这是一个 HTTP 服务的配置优先级故障。基础配置看起来正确，但高优先级环境覆盖使实际生效配置错误；配置协调器会继续维护该状态，因此仅重启或只改低优先级配置不能完成任务。

公开题面只给出症状、影响、目标和约束，没有公开覆盖文件名、正确端口、预期 repair action 或 verifier check 名称。Agent 需要先通过公开工具读取 live state，再完成持久修复。

最终 Agent 观察到了有效配置和异常状态，但没有清除高优先级覆盖并验证协调器边界后的状态。失败 checks：`business_operation`、`effective_state`、`reconciler_persistence`。

## Case 2：HTTP 下游依赖超时

这是一个服务调用下游依赖过慢导致业务请求失败的任务：注入后客户端超时为 150ms，而下游延迟为 900ms，业务接口返回 502。正确修复需要完成声明的 prepare/apply 阶段，并恢复下游延迟与客户端超时之间的健康关系，同时验证重启后的持久性。

Agent 成功读取到 `client_timeout_ms=150` 和 `dependency_delay_ms=900`，但猜测了未被工具协议接受的 action，没有完成 prepare/apply，因此注入状态保持不变。失败 checks：`business_operation`、`dependency_delay`、`persistence`。

## Agent 评测配置

两题使用相同的 Agent 运行条件：

```yaml
agent: langchain-react-agent
model: deepseek-v4-flash
max_steps: 60
timeout_sec: 180
temperature: 0
protocol_id: opsbench-agent-v1
artifact_mode: trusted
```

当前项目通过阿里百炼兼容 OpenAI API endpoint 调用模型；仓库中不包含 API Key。Agent 只读取 `public/task.md`、`public/tools.json`，并在目标容器内执行公开工具。`agent_start.json` 中记录了 prompt、工具契约和 Agent runtime digest，可用于复现实验条件。

## 如何查看 Agent 做了什么

每个结果目录包含：

```text
details.jsonl                  Runner phase、verifier checks 和最终 failure_type
summary.json                   统计汇总
traces/<run-id>/trace/
  agent_start.json             模型、步数、超时和 digest
  agent_messages.jsonl         ReAct 消息及工具调用
  tool_calls.jsonl             工具输入、返回值和耗时
  agent_diagnosis.json         Agent 读取到的诊断信号
  agent_result.json            Agent 进程结果
```

建议专家先看 `results/*/summary.json`，再对照 `results/*/traces/*/trace/tool_calls.jsonl` 和对应 case 的 `public/tools.json`，最后查看隐藏 `evaluator/verify.py` 及 `results/runtime-controls/`。

## 结果解释

```text
case_status=evaluable       case 可以用于模型评测
model_result=passed         Agent 完成任务且 verifier 通过
model_result=failed         Agent 运行完成，但 verifier 未通过
failure_type=task_failure   正常的任务失败，不是基础设施错误
```

本批结果：

```text
case_status: 2/2 evaluable
Agent completed: 2/2
model passed: 0/2
model failed: 2/2
infrastructure errors: 0
timeouts: 0
cleanup failures: 0
```

这两个结果可以说明当前 Agent 在这两个任务上没有完成修复，但不应仅凭两题推断模型整体能力或难度分层。

## 安全与完整性说明

- 没有提交 `.env`、API Key、宿主机凭据或 Docker socket。
- case 的 `evaluator/`、`scenario.json` 和 `scripts/` 保留在完整分析包中；对外发布时应只发布 public package。
- `runtime-controls` 中的 `no-op`、`wrong-fix`、`partial-fix` 等失败是预期的负向控制结果；runtime gate 的总体通过表示这些控制行为符合预期。
- 生成模式为 `trusted`：Compose、生命周期脚本和 verifier 来自已注册可信能力，避免把 artifact 生成错误混入本次文档驱动与 Agent 评测结果。
