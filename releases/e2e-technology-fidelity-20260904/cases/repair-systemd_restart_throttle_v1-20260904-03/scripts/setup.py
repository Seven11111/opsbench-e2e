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
(runtime/'opsbench.service').write_text('[Unit]\\nDescription=OpsBench native systemd service\\nStartLimitIntervalSec=10\\nStartLimitBurst=3\\n[Service]\\nType=simple\\nExecStart=/usr/local/bin/python /opt/opsbench/service.py\\nEnvironment=OPSBENCH_SYSTEMD_CHILD=1\\nRestart=on-failure\\nRestartSec=0.2\\n'); compose_exec('target','systemctl --user daemon-reload; systemctl --user reset-failed opsbench.service; systemctl --user start opsbench.service')
