# 新场景 E2E 生成与评测报告

## 结论

本轮尝试了 36 组文档/能力输入，冻结了 10 个 `case_status=evaluable` case。
统一使用 DeepSeek Flash、60 steps、600 秒、temperature=0 的容器 Agent 评测；成功 2/10，完成率 100.00%，超时 0.0。

`target_difficulty` 只是结构化设计难度，本轮未做 Agent panel 经验校准。

## 固定评测条件

- generator: `deepseek-v4-flash`；source/review: `qwen3.7-flash`；Judge 最多 3 轮。
- agent: `deepseek-v4-flash`，60 步，600 秒，temperature=0。
- 每个 case 通过 static validation、baseline/injection、no-op、oracle、negative controls、repeat 和 cleanup 后才进入 manifest。
- 本轮 10/10 Agent 完成，0 timeout，0 infrastructure error，0 cleanup failure。

## 冻结的 10 个 case

| Case | Primitive | Domain | Target difficulty | Model result | Score | Duration(s) |
|---|---|---|---|---:|---:|---:|
| `candidate_linux_file_lock_v1_001` | `linux_file_lock_v1` | linux | medium (5) | failed | 0.35 | 154.796 |
| `candidate_linux_upload_permission_v1_001` | `linux_upload_permission_v1` | linux | easy (3) | failed | 0.8 | 111.954 |
| `candidate_prometheus_file_sd_001` | `prometheus_scrape_target_v1` | observability | medium (5) | failed | 0.25 | 211.562 |
| `dynamic_app_config_precedence_v1_000001` | `app_config_precedence_v1` | configuration | hard (8) | passed | 1.0 | 102.734 |
| `dynamic_app_stale_pid_v1_000001` | `app_stale_pid_v1` | configuration | medium (5) | passed | 1.0 | 41.0 |
| `dynamic_http_upstream_timeout_v1_000001` | `http_upstream_timeout_v1` | network | medium (5) | failed | 0.0 | 127.625 |
| `dynamic_linux_memory_growth_v1_000001` | `linux_memory_growth_v1` | linux | medium (5) | failed | 0.0 | 153.0 |
| `dynamic_linux_temp_permission_v1_000001` | `linux_temp_permission_v1` | linux | easy (3) | failed | 0.0 | 140.063 |
| `dynamic_tls_hostname_mismatch_v1_000001` | `tls_hostname_mismatch_v1` | tls | hard (10) | failed | 0.0 | 176.531 |
| `fluentbit_backpressure_v1_001` | `fluentbit_backpressure_v1` | logging | hard (9) | failed | 0.5 | 185.219 |

## 生成筛选

- 生成过程保留在每个编号 job 目录：原始文档、证据、Judge/rejection、case package 与 runtime controls。
- 严格证据门禁拒绝了来源角色不匹配、修复证据不足、文档与能力不对应等候选；这类拒绝不会进入最终 manifest。
- 3 个初始静态有效但缺少公共 oracle 的候选在补齐通用公共工具适配和显式 `agent_service` 后重新通过 gate。

## 模型评测解释

本轮结果为 2 passed、8 model_failed。失败项均为 Agent 已退出且 Docker/verifier 执行完成后的 `task_failure`，不是请求超时或基础设施错误；具体 check、trace 和原始日志见 `results/flash-60-600-10/details.jsonl` 与各 case trace。

## 可复现入口

```powershell
opsbench validate-e2e --case-root tmp/e2e-new-10-quality-20260831/combined-10/cases
opsbench eval e2e-manifest --case-root tmp/e2e-new-10-quality-20260831/combined-10/cases --sample-size 10 --sample-seed 42 --output tmp/e2e-new-10-quality-20260831/combined-10/e2e_manifest.json
opsbench eval e2e-run --manifest tmp/e2e-new-10-quality-20260831/combined-10/e2e_manifest.json --agent-config tmp/e2e-new-10-quality-20260831/flash-60-600.yaml --output-dir tmp/e2e-new-10-quality-20260831/results/flash-60-600-10
```
