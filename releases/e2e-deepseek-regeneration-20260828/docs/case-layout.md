# Case package layout

每个目录是一个可独立运行的完整 E2E case。为便于专家审阅，本 release 同时保留公开输入和本地运行所需的隐藏组件。

```text
cases/<case>/
├── manifest.yaml                 # case 元数据、标签、难度和生命周期
├── public/
│   ├── task.md                   # Agent 可见任务
│   └── tools.json                # Agent 可见工具契约
├── environment/
│   ├── docker-compose.yaml       # 运行环境
│   ├── Dockerfile
│   ├── runtime/                  # 目标服务和运行时控制
│   └── agent/                    # 容器内 Agent 入口/依赖
├── scripts/
│   ├── setup.py
│   ├── inject.py
│   ├── check_injected.py
│   └── cleanup.py
└── evaluator/
    ├── scenario.json             # hidden 场景参数
    ├── labels.yaml
    ├── common.py
    ├── faults.py
    └── verify.py                 # hidden verifier
```

Agent 正常只能访问 `public/task.md`、`public/tools.json`、运行时公开工具和 trace 目录。`scenario.json`、`evaluator/` 和宿主机 `.env` 不属于 Agent 输入。

结果与生成记录不放进 case 包，以免改变 case 的运行边界：

```text
provenance/<case>/                # 生成与来源
results/runtime-gate/<case>.json  # Docker 质量门
results/flash/<case>/             # Agent 结果和 trace
```

完整 case 包可以由 `opsbench validate-e2e` 静态检查；运行时则由 E2E runner 按 manifest 顺序 provision、注入、运行 Agent、verify 和 cleanup。
