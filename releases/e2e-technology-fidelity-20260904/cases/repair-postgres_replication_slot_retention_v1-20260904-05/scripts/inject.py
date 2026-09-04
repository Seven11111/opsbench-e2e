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
compose_exec('target','psql -h db -U opsbench -d app -c \\"SELECT pg_create_physical_replication_slot(\'opsbench_hold\', true); SELECT slot_name,restart_lsn FROM pg_replication_slots WHERE slot_name LIKE \'opsbench_%\'; INSERT INTO wal_probe(payload) SELECT repeat(\'x\',8192) FROM generate_series(1,5000); SELECT pg_switch_wal(); CHECKPOINT;\\"')
pg_replication_slots='pg_replication_slots'
