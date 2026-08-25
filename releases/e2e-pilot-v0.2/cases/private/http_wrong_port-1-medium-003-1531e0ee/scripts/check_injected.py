from __future__ import annotations
import json
import sys
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
config = json.loads((case_dir / "environment" / "runtime" / "config.json").read_text(encoding="utf-8"))
expected = {'port': 18081}
if config != expected:
    raise SystemExit("injection check failed")
(case_dir / "environment" / "runtime" / "status.json").write_text(json.dumps({"healthy": False}, indent=2), encoding="utf-8")
