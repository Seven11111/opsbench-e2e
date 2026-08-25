from __future__ import annotations
import json
import sys
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
runtime = case_dir / "environment" / "runtime"
(runtime / "config.json").write_text(json.dumps({'runaway': True, 'work_units': 50000}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(runtime / "status.json").write_text(json.dumps({"healthy": False}, indent=2) + "\n", encoding="utf-8")
