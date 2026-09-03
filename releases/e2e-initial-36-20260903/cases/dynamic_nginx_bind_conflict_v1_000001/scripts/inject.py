from __future__ import annotations
import json
import sys
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
runtime = case_dir / "environment" / "runtime"
(runtime / "nginx.conf").write_text(
    (runtime / "nginx.conf").read_text(encoding="utf-8").replace("18081", "18080"),
    encoding="utf-8",
)
(runtime / "fault.json").write_text(json.dumps({'mode': 'bind_conflict'}, indent=2) + "\n", encoding="utf-8")
(runtime / "fault_progress.json").write_text(json.dumps({'blocker_spawned': False}, indent=2) + "\n", encoding="utf-8")
(runtime / "status.json").write_text(json.dumps({"healthy": False}) + "\n", encoding="utf-8")
(runtime / "nginx-error.log").write_text("", encoding="utf-8")
