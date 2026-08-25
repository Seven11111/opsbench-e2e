# E2E Pilot 汇报记录

## 数据状态

- 数据集版本：`opsbench-e2e-benchmark-v1`
- 发布状态：`pilot_incomplete`
- 当前 case 数量：11
- 正式目标：48
- 经验难度状态：`not_calibrated`

当前 pilot 不是最终 benchmark。它用于验证 case package、文档来源、静态
校验和评测协议，能力范围和难度分布尚未达到正式论文实验要求。

## 能力分布

| 能力范围 | 数量 |
|---|---:|
| HTTP 错误端口 | 4 |
| Linux CPU runaway v1 | 4 |
| Linux CPU runaway v2 | 1 |
| Nginx 端口冲突 | 1 |
| PostgreSQL 缺失索引 v2 | 1 |

当前分布为 easy 1、medium 9、hard 1。旧版 HTTP/CPU case 的结构化难度
评分不能作为模型难度区分实验结论。

## 验证状态

11 个 case 均通过静态 package validation。对应的 3 个 demo case 已完成
Docker runtime gate，包括 baseline、故障注入、no-op、oracle、错误修复、
部分修复、restart-only、repeat 和 cleanup。其余 8 个 case 仍标记为
`runtime_pending`，不会被表述为完整 runtime gate 通过。

## 后续工作

正式 benchmark 需要：

1. 纳入 hard calibration 中已有的能力范围；
2. 为每个能力补足 4 个实质不同的 case；
3. 重新执行每题 runtime gate；
4. 冻结 36 个开发集和 12 个测试集；
5. 使用相同 Agent 配置比较 Flash 与 Pro。
