# Results Layout

## Runtime gate

`runtime-gate/` contains the full control reports. The four reports marked as
passed include baseline, injection, no-op, oracle, restart-only, wrong-fix,
partial-fix, repeat, and cleanup outcomes. The Kafka report is retained as a
failure artifact and records the consumer-group baseline problem.

## GLM evaluation

`glm-4.7/` contains one evaluation directory per runtime-ready case. Each
directory contains:

- `summary.json`: metrics and manifest information;
- `details.jsonl`: one result record for the case;
- `traces/`: Agent start/result, messages, tool calls, and process logs.

The evaluation used the same packaged ReAct Agent and the same 60-step,
300-second configuration for all cases. The aggregate result is
`results/summary.json`.

The PostgreSQL lock, PostgreSQL pool, and Redis verifiers currently assign four
checks a weight of `0.2` each. Their raw score is therefore `0.8` even when all
checks pass. The boolean `passed` field is the authoritative task result for
this pilot; the weight normalization should be fixed before paper statistics
are produced.
