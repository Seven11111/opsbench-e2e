from __future__ import annotations
import json
import sys
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
runtime = case_dir / "environment" / "runtime"
(runtime / "worker.conf").write_text(json.dumps({'enabled': False, 'work_units': 30000}, indent=2) + "\n", encoding="utf-8")
(runtime / "status.json").write_text(json.dumps({"healthy": True}) + "\n", encoding="utf-8")
