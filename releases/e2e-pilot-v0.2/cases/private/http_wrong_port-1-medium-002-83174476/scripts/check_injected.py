from __future__ import annotations
import json
import sys
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
config = json.loads((case_dir / "environment" / "runtime" / "config.json").read_text(encoding="utf-8"))
expected = {'port': 18191}
if config != expected:
    raise SystemExit("injection check failed")


import urllib.error
import urllib.request

try:
    with urllib.request.urlopen("http://127.0.0.1:18190/health", timeout=3) as response:
        if response.status == 200:
            raise SystemExit("injected HTTP fault was not observed")
except urllib.error.URLError:
    pass

(case_dir / "environment" / "runtime" / "status.json").write_text(json.dumps({"healthy": False}, indent=2), encoding="utf-8")
