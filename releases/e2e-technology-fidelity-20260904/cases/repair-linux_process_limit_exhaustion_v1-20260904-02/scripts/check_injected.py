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
native=target_native()
try: current=int(native.get('pids.current')); maximum=int(native.get('pids.max'))
except (TypeError,ValueError): raise SystemExit('native cgroup PID counters are unavailable')
if current < maximum - 4 or native.get('process_creation') != 'EAGAIN' or int(native.get('child_processes',0)) < 80: raise SystemExit('native PID budget pressure was not observed')
