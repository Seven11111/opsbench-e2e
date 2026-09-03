from pathlib import Path
import os
import shlex
import subprocess
import time
import urllib.request

root = Path(__file__).parents[1]
compose = [*shlex.split(os.environ.get('OPSBENCH_COMPOSE_BIN', 'docker-compose' if os.name == 'nt' else 'docker compose')), '-f', str(root / 'environment/docker-compose.yaml')]
if 'fault' not in (root / 'environment/runtime/sink.mode').read_text(encoding='utf-8'):
    raise SystemExit('downstream backpressure injection not observed')
def sink_count():
    result = subprocess.run([*compose, 'exec', '-T', 'sink', 'sh', '-lc', 'cat /tmp/sink.received'], capture_output=True, text=True, check=False)
    try:
        return int((result.stdout or '0').strip() or '0')
    except ValueError:
        return 0
before_count = sink_count()
try:
    request = urllib.request.Request('http://127.0.0.1:19880/', data=b'{"message":"injected"}', headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(request, timeout=5).read(1000)
except Exception:
    pass
time.sleep(2)
if sink_count() > before_count:
    raise SystemExit('injected output unexpectedly delivered a record')
