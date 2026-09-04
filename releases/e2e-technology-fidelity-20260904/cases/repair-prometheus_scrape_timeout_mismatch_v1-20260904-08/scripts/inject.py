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
(runtime/'prometheus.yml').write_text("global:\\n  scrape_interval: 5s\\n  scrape_timeout: 10s\\nscrape_configs:\\n  - job_name: opsbench-target\\n    static_configs:\\n      - targets: ['target:8080']\\n"); subprocess.run(['curl','--noproxy','*','-fsS','-X','POST','http://127.0.0.1:9090/-/reload'],check=False); scrape_timeout_errors=json.dumps(json.load(urllib.request.urlopen('http://127.0.0.1:9090/api/v1/targets?state=active',timeout=10)))
