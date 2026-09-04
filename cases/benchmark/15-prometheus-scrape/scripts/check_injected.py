import json
import time
import urllib.request

def active_target_health(instance: str) -> str | None:
    payload = json.load(urllib.request.urlopen(
        'http://127.0.0.1:19090/api/v1/targets?state=active', timeout=5,
    ))
    for target in payload.get('data', {}).get('activeTargets', []):
        labels = target.get('labels', {})
        if labels.get('job') == 'opsbench-target' and labels.get('instance') == instance:
            return str(target.get('health') or '').lower()
    return None

for _ in range(12):
    try:
        if active_target_health('missing-exporter:19999') not in {'up'}:
            break
    except Exception:
        pass
    time.sleep(1)
else:
    raise SystemExit('injected target unexpectedly healthy')
