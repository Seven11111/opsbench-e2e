from __future__ import annotations
import base64
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

case_dir = Path(sys.argv[sys.argv.index("--case-dir") + 1]).resolve()
# Windows Docker Desktop installations in this project expose the legacy
# executable reliably even when the ``docker compose`` plugin is unavailable.
# The runner still injects an explicit binary, but this fallback keeps the
# generated lifecycle scripts usable when invoked directly by a reviewer.
compose = shlex.split(os.environ.get("OPSBENCH_COMPOSE_BIN", "docker-compose" if os.name == "nt" else "docker compose"))
compose_file = str(case_dir / "environment/docker-compose.yaml")
def target(command: str, *, user: str = "opsbench", check: bool = True):
    return subprocess.run([*compose, "-f", compose_file, "exec", "-T", "--user", user, "target", "sh", "-lc", command], check=check, capture_output=True, text=True, encoding="utf-8", errors="replace")
def target_python(code: str, *, check: bool = True):
    # docker-compose.exe on Windows may split a direct ``python -c`` payload
    # at spaces or quotes before it reaches the container.  Base64 keeps the
    # trusted generated code transport-safe; the tiny bootstrap itself has no
    # spaces, so the Compose executable cannot split its argument.
    encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")
    bootstrap = f"exec(__import__('base64').b64decode('{encoded}'))"
    return subprocess.run([*compose, "-f", compose_file, "exec", "-T", "--user", "opsbench", "target", "python", "-c", bootstrap], check=check, capture_output=True, text=True, encoding="utf-8", errors="replace")
target_python("import json; assert json.load(open('/runtime/config.json'))['growth_enabled']")
