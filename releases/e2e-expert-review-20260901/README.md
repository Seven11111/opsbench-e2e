# E2E 专家复核后的 6 个修补 Case

本 release 保存 6 个根据专家意见完成语义对齐和 runtime 修补的 E2E case：

| Case | 能力 | 当前状态 |
|---|---|---|
| `01-file-lock` | Linux 文件锁 | `evaluable` |
| `19-memory-growth` | Linux 内存持续增长 | `evaluable` |
| `15-prometheus-scrape` | Prometheus 目标抓取 | `evaluable` |
| `16-fluentbit-backpressure` | Fluent Bit 下游背压 | `evaluable` |
| `23-upstream-timeout` | HTTP 上游延迟/超时 | `evaluable` |
| `27-upload-chmod` | 上传目录权限 | `evaluable` |

## 验证结果

6 个 case 均通过：

- 静态 schema、安全边界和任务-工具-verifier 对齐校验；
- Docker baseline、故障注入和注入检查；
- oracle 正向修复；
- no-op、wrong-fix、partial-fix、restart-only 负面控制；
- repeat 稳定性；
- cleanup。

完整结果见 [`results/runtime_controls.json`](results/runtime_controls.json)，运行 trace 见 `results/control_traces/`。`evaluable` 表示可以进入模型评测，不代表已经完成模型难度校准或专家最终批准为正式 benchmark。

## 本轮关键修补

- 文件锁 verifier 改为检查真实 `fcntl` 锁状态，而不是只看配置标志。
- 内存增长 verifier 改为检查实时 metrics；partial fix 只提高容量、不关闭持续增长机制。
- Prometheus verifier 改为检查真实 Prometheus readiness、目标状态和业务指标。
- Fluent Bit 改为真实 HTTP input → Forward sink 业务链路，并检查下游投递计数和重启后恢复。
- HTTP timeout 改为检查真实 `/orders` 请求状态和耗时；同步修复发布包中遗漏的 `import time`。
- 上传权限 verifier 同时检查真实上传、服务身份、组写权限和禁止 world-writable。

## 目录

每个目录都是可复现的 OpsBench 风格 case package，包含：

```text
manifest.yaml
public/task.md
public/tools.json
environment/
scripts/
evaluator/
```

公开 task 不直接给出根因或唯一修复动作；完整 scenario、注入脚本和 verifier 用于本地内部评测。运行前请使用本地 `opsbench-factory` 的 runner，并在本机配置 API Key，不要把 Key 写入仓库。
