import json
import time
import urllib.request

for _ in range(12):
    try:
        payload = json.load(urllib.request.urlopen(
            'http://127.0.0.1:19090/api/v1/query?query=up%7Bjob%3D%22opsbench-target%22%7D',
            timeout=5,
        ))
        values = payload.get('data', {}).get('result', [])
        if not values or values[0].get('value', [None, '0'])[1] != '1':
            break
    except Exception:
        pass
    time.sleep(1)
else:
    raise SystemExit('injected target unexpectedly healthy')
