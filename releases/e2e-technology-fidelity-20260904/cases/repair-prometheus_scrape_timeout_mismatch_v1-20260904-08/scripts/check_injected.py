import json, os, shlex, subprocess, sys, time, urllib.request
from pathlib import Path
root=Path(__file__).parents[1]
runtime=root/'environment/runtime'
def reload_target():
    with urllib.request.urlopen('http://127.0.0.1:8080/reload',timeout=10) as response:
        assert response.status==200
def target_native():
    with urllib.request.urlopen('http://127.0.0.1:8080/native',timeout=10) as response:
        return json.loads(response.read().decode())
def compose_exec(service, command):
    compose=shlex.split(os.environ.get('OPSBENCH_COMPOSE_BIN','docker compose'))
    return subprocess.run([*compose,'-f',str(root/'environment/docker-compose.yaml'),'exec','-T',service,'sh','-lc',command],capture_output=True,text=True,check=False,timeout=45)
def public_probe():
    with urllib.request.urlopen('http://127.0.0.1:8080/business',timeout=10) as response:
        return response.status
payload=json.load(urllib.request.urlopen('http://127.0.0.1:9090/api/v1/targets?state=active',timeout=10)); target=next((item for item in payload.get('data',{}).get('activeTargets',[]) if item.get('labels',{}).get('job')=='opsbench-target'),{}); error=str(target.get('lastError') or ''); scrape_timeout_errors=error
if target.get('health') != 'down' or not error or ('timeout' not in error.lower() and 'context deadline' not in error.lower()): raise SystemExit('native Prometheus scrape timeout was not observed')
