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
(runtime/'strict-config.json').write_text('{"commit_enabled": false}\n'); reload_target(); compose_exec('target',"printf 'event-1\nevent-2\nevent-3\nevent-4\nevent-5\nevent-6\n' | kcat -b kafka:9092 -t opsbench-events -P"); time.sleep(3); describe=compose_exec('kafka','/opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group opsbench-group')
