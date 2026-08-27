from pathlib import Path
import json, os, shlex, subprocess, sys, time

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve(); runtime = case_dir / "environment/runtime"
compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker-compose")); cf = str(case_dir / "environment/docker-compose.yaml")
def target(command):
    result = subprocess.run([*compose, "-f", cf, "exec", "-T", "target", "sh", "-lc", command], capture_output=True, text=True, check=False, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"target command failed: {command}")
    return result
(runtime / "refresh.env").write_text("schema_version=1\n", encoding="utf-8")
(runtime / "state.json").write_text(json.dumps({"mode":"injected","fault":"refresh_schema_drift"}, indent=2) + "\n", encoding="utf-8")
target("if [ -f /runtime/refresh-worker.pid ]; then kill $(cat /runtime/refresh-worker.pid) 2>/dev/null || true; fi; rm -f /runtime/refresh-worker.pid")
time.sleep(5)
