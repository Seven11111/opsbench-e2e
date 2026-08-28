# E2E DeepSeek regeneration release

本 release 保存了 `opsbench-factory` 在 2026-08-28 重新生成的两个动态 E2E case，供专家审阅生成流程、来源追溯、Docker 可评测性和 Agent 结果。

这不是已经完成难度校准的正式 benchmark，而是一次可复核的 smoke/regeneration release。两个 case 都通过了静态校验和 Docker runtime gate，因此 `case_status=evaluable`；Agent 评测结果另行记录为 `model_result=passed|failed`。

## Case 概览

| Case | 来源能力 | 目标难度 | Source Judge | Runtime gate | DeepSeek Flash |
|---|---|---:|---:|---:|---:|
| `dynamic_app_config_precedence_v1_000001` | `app_config_precedence_v1` | hard / 8 | 1 轮通过，4.84/5 | 通过 | failed（任务失败） |
| `dynamic_http_dependency_timeout_slo_v1_000001` | `http_dependency_timeout_slo_v1` | medium / 6 | 第 1 轮失败，第 2 轮通过，4.74/5 | 通过 | passed |

## 两个任务分别做什么

### App configuration precedence

公开题面只告诉 Agent：服务没有处于健康的运行状态，需要通过公开运行时工具诊断、恢复业务操作，并确认修复在 reconciler 生命周期边界之后仍然有效。题面没有公开根因、配置层或具体修复键。

这个 case 的内部故障是：有效运行时状态被高优先级配置覆盖，直接修改较低层配置或只重启不能形成持久修复。Verifier 分别检查业务恢复、有效状态和 reconciler 后的持久性。

Flash Agent 完成了执行，并使业务检查和有效状态检查通过，但没有消除 reconciler 会重新施加的覆盖状态，最终 `reconciler_persistence` 失败。因此这是正常的 `model_result=failed`，不是 Docker、API 或 Agent 启动错误。

### HTTP dependency timeout / SLO

公开题面描述一个 HTTP 业务操作异常，并要求恢复业务请求，同时保持公开的请求延迟目标低于 600 ms。题面没有公开具体依赖参数、配置键或预期修复动作。

这个 case 的内部故障是下游依赖延迟与客户端 SLO/超时配置不匹配。Verifier 检查业务请求、延迟 SLO、依赖延迟信号和持久性。

Flash Agent 完成了诊断和修复，四项 verifier check 全部通过，`model_result=passed`。

## 实际生成与评测流程

```text
完整文档 EvidenceBundle
        |
        v
单候选 ScenarioSpec 生成（dynamic，group_size=1）
        |
        v
Source / Evidence Judge
        | 失败：保留具体反馈并回传生成上下文，最多 3 轮
        v
trusted renderer 编译环境、生命周期脚本和 verifier
        |
        v
静态 schema / 安全 / 隐藏信息校验
        |
        v
Docker runtime gate：provision → setup → baseline → inject
        → check_injected → no-op/oracle/negative controls → cleanup
        |
        v
case_status=evaluable
        |
        v
LangChain ReAct Agent（Flash60）运行公开 task/tools
        |
        v
model_result=passed|failed
```

本次使用 `artifact_mode=trusted`：模型负责生成 ScenarioSpec、公开题面和证据引用，Docker、脚本及 verifier 由当前项目的可信 renderer 生成。这样可以把“文档驱动/题面质量”与“模型自由生成 Docker 文件的工程风险”分开观察。

Source Judge 修复时保留当前候选、完整证据上下文、前一轮反馈和版本记录。HTTP case 第 1 轮的主要问题是证据与根因字段不匹配，记录在 `provenance/http-timeout-slo/reviews/model_reviews.jsonl`，第 2 轮通过后才继续编译。

## 结果含义

- `case_status=evaluable`：case 能启动、注入出的故障真实存在、Verifier 能识别正确/错误状态，并完成清理。
- `model_result=passed`：Agent 完成任务且最终 verifier 通过。
- `model_result=failed`：Agent 执行完成，但至少一个最终 verifier check 未通过。
- 本 release 没有把 Agent 失败错误地标记为基础设施失败；具体 phase、check、耗时和日志见 `results/flash/` 与 `results/runtime-gate/`。

## 结果文件

```text
e2e-deepseek-regeneration-20260828/
├── cases/
│   ├── app-config-precedence/       # 完整 case package，含 hidden evaluator
│   └── http-timeout-slo/            # 完整 case package，含 hidden evaluator
├── provenance/
│   ├── app-config-precedence/       # 文档、Evidence、候选、Judge、修订、报告
│   └── http-timeout-slo/
├── results/
│   ├── runtime-gate/                # Docker runtime_controls.json
│   ├── flash/                       # summary、details、Agent trace
│   └── manifests/                   # 本次运行使用的 case manifest
├── agents/langchain-react-agent/    # 评测时使用的 ReAct Agent 入口
├── configs/e2e-flash-60.yaml        # Flash60 配置
├── dataset_manifest.json
└── docs/
    ├── generation-and-evaluation-flow.md
    └── case-layout.md
```

`provenance/*/evidence/bundles/` 中保留了来源 URL、content hash、claim/evidence span 和选择信息；`candidates/`、`reviews/`、`revisions/` 可用于重算每一轮生成与审核过程。原始 API Key、`.env` 和宿主机凭据没有进入仓库。

## 本次 Agent 配置

两题使用相同的评测入口和 `flash_60` 配置：

```yaml
model: deepseek-v4-flash
max_steps: 60
agent_timeout_sec: 180
temperature: 0
```

评测入口是项目中的 `agents/langchain-react-agent/run.py`，内部调用 LangChain/LangGraph 的 ReAct agent；trace 中可看到每次工具调用、返回值和最终 verifier 结果。运行时 API Key 只从本地环境读取，没有写入本 release。

## 重新检查

在 `opsbench-factory` 环境中，可先执行静态检查：

```powershell
opsbench validate-e2e `
  --case-root releases/e2e-deepseek-regeneration-20260828/cases
```

若要在新的工作目录重新生成本地评测 manifest，应使用仓库中的完整 case 目录作为 `--case-root`，不要直接复用结果文件中的本机绝对路径。已有结果是本次真实运行的冻结记录；重新运行时应保留新的 agent config、case digest 和 trace，不能与本次结果直接拼接。

