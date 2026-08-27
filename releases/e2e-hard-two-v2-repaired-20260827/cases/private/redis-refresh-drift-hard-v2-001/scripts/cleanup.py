from pathlib import Path
import json, sys
import os, shlex, subprocess
case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve(); runtime = case_dir / "environment/runtime"
(runtime / "refresh.env").write_text("", encoding="utf-8")
(runtime / "state.json").write_text(json.dumps({"mode":"baseline"}, indent=2) + "\n", encoding="utf-8")
compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker-compose")); cf = str(case_dir / "environment/docker-compose.yaml")
subprocess.run([*compose, "-f", cf, "exec", "-T", "target", "sh", "-lc", "if [ -f /runtime/refresh-worker.pid ]; then kill $(cat /runtime/refresh-worker.pid) 2>/dev/null || true; fi; rm -f /runtime/refresh-worker.pid"], capture_output=True, text=True, check=False, timeout=30)
