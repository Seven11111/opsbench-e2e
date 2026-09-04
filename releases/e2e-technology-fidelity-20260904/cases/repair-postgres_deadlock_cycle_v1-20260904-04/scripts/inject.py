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
deadlock_sql='(echo \\"BEGIN; SET deadlock_timeout=\'60s\'; SELECT id FROM orders WHERE id=1 FOR UPDATE; SELECT pg_sleep(2); SELECT id FROM orders WHERE id=2 FOR UPDATE; SELECT pg_sleep(120);\\" | PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app >/tmp/a.log 2>&1) & (echo \\"BEGIN; SET deadlock_timeout=\'60s\'; SELECT id FROM orders WHERE id=2 FOR UPDATE; SELECT pg_sleep(2); SELECT id FROM orders WHERE id=1 FOR UPDATE; SELECT pg_sleep(120);\\" | PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app >/tmp/b.log 2>&1) &'; compose_exec('target',deadlock_sql); time.sleep(3)
