# Case layout

Each case exposes only `public/task.md`, `public/tools.json`, the runtime tool boundary, and a writable trace directory to the Agent. Compose, setup/injection scripts, scenario, labels, and `evaluator/verify.py` remain outside the public task view.

Lifecycle: `validate -> provision -> setup -> baseline_check -> inject -> check_injected -> run_agent -> verify -> cleanup`

The runtime gate exercises no-op, oracle, wrong-fix, partial-fix, restart-only, repeat, and cleanup behavior.
