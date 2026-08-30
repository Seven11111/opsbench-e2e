# E2E Fairness Repair v2：三 Case 评审包

本 release 包含针对专家反馈修订后的 3 个 E2E case。它们用于检查
“公开任务、公开工具、runtime oracle 与隐藏 verifier”是否保持一致，
不是新的正式 benchmark 版本。

## Cases

| Case | 场景 | 修订重点 | Runtime 状态 |
|---|---|---|---|
| `repaired_app_config_precedence_v1_001` | 配置优先级导致有效配置异常 | 检查真实有效状态和 reconciler 持久性 | `evaluable` |
| `repaired_app_stale_pid_v1_001` | stale PID 与真实进程身份不一致 | 使用通用生命周期工具和真实 PID 身份检查 | `evaluable` |
| `repaired_http_dependency_timeout_slo_v1_001` | 下游延迟导致请求违反 SLO | 删除隐藏 250ms 阈值，统一使用公开 600ms 预算 | `evaluable` |

每个 case 都是完整的本地评测包，包含 `manifest.yaml`、公开 task/tools、
Compose 环境、注入与清理脚本，以及隐藏 evaluator。公开 task 不包含根因、
精确修复动作或内部 verifier check 名称。

## 本次修订

### HTTP timeout

之前 verifier 同时要求公开的延迟目标和隐藏的 `dependency_delay <= 250ms`，
导致合理的恢复方案也可能被拒绝。现在：

- 公开契约只有一个 `request_latency_budget_ms=600`；
- baseline 客户端超时为 `500ms`，满足公开契约；
- 注入使用高延迟和过短客户端超时制造故障；
- verifier 检查业务恢复、公开延迟 SLO、timeout policy 和持久性；
- 不再使用隐藏的 250ms 下限。

### stale PID

之前公开 oracle 调用了 primitive 专用的隐藏动作。现在 oracle 只通过公开能力：

```text
service_list
→ service_status / signal_view / business_probe
→ service_manage(action=restart)
→ 再次观察业务和真实进程身份
```

工具参数使用动态 service ID，生命周期动作使用公开闭合枚举，不要求 Agent 猜
测 `restore_service_identity` 等内部动作。

### 通用门禁

生成和发布前增加了：

- verifier 数值阈值 provenance 检查；
- public oracle 隐藏动作输入检查；
- task/tool/verifier 对齐检查；
- baseline 必须满足与修复后相同的公开契约；
- 多个合理修复路径和负向控制的统一记录。

这些规则已经写入源项目的版本化经验文件，后续其他能力生成也会复用。

## Runtime gate 结果

每个 case 通过了以下控制：

```text
baseline → inject → check_injected
→ no-op → oracle → negative controls
→ repeat × 2 → cleanup
```

结果摘要：

- 3/3 case 为 `evaluable`；
- runtime controls 总计 28 次；
- no-op、wrong-layer/错误修复、partial-fix、restart-only 均按预期失败；
- oracle 和 repeat 均按预期通过；
- public-tool oracle 均通过；
- cleanup 无 case 容器、网络和 volume 残留。

本次 smoke gate 每个 case 使用 1 次 public-tool oracle，repeat 控制仍执行 2 次。
正式 benchmark 可将 public oracle 重复次数提高到 3 次。

## 目录说明

```text
cases/                         完整三 case 包
candidates/candidates.jsonl   候选记录
provenance/                    文档、证据、bundle、review provenance
reviews/                       修订评审记录
reports/runtime_controls.json  三 case 合并 runtime 结果
reports/runtime_controls_*.json 各 case 独立结果
reports/static_validation.jsonl 静态校验结果
reports/repair_summary.json    本次修订摘要
manifest.json                  run 和 case digest
```

为避免 Windows 深层路径和重复日志造成仓库膨胀，原始 Docker 控制 trace 未复制
到本 release；完整 trace 仍保留在源项目本地运行目录：

```text
tmp/expert-fairness-3-repaired-20260830-v9/reports/control_traces/
```

## 本地复现

在 `opsbench-factory` 环境中执行：

```powershell
opsbench validate-e2e --case-root cases/repaired_app_config_precedence_v1_001
opsbench runtime-gate-e2e `
  --run-dir . `
  --case-root cases/repaired_app_config_precedence_v1_001 `
  --execution-mode container `
  --public-oracle-repeats 1
```

对其他两个 case 替换 `--case-root` 即可。模型评测尚未包含在本 release 的修订
动作中；本 release 首要证明的是 case 本身可运行、verifier 可区分正确和错误
修复，以及公开工具路径可达。

