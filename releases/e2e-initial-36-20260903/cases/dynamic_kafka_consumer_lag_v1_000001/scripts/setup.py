from pathlib import Path
import json, os, shlex, subprocess, sys, time
case_dir=Path(sys.argv[sys.argv.index('--case-dir')+1]).resolve()
root=case_dir/'environment/runtime'
compose=shlex.split(os.environ.get('OPSBENCH_COMPOSE_BIN','docker-compose'))
cf=str(case_dir/'environment/docker-compose.yaml')
def exec_target(command):
    # Keep the long-lived PostgreSQL fault sessions detached from the Compose
    # exec stdout handle.  The command is still emitted by the trusted
    # renderer, but is normalized here to avoid nested shell quoting issues on
    # Windows Docker Desktop.
    if 'opsbench-lock-holder' in command and 'pg_advisory_lock' in command:
        command = "nohup env PGPASSWORD=opsbench-local-only PGAPPNAME=opsbench-lock-holder psql -h db -U opsbench -d app -c 'SELECT pg_advisory_lock(424242); SELECT pg_sleep(600);' >/tmp/lock-holder.log 2>&1 </dev/null &"
    elif 'opsbench-pool-holder' in command and 'pg_sleep' in command:
        command = "for n in $(seq 1 14); do nohup env PGPASSWORD=opsbench-local-only PGAPPNAME=opsbench-pool-holder psql -h db -U opsbench -d app -c 'SELECT pg_sleep(600)' >/tmp/pool-$n.log 2>&1 </dev/null & done"
    return subprocess.run([*compose,'-f',cf,'exec','-T','target','sh','-lc',command],capture_output=True,text=True,check=False,timeout=30)
def exec_broker(command): return subprocess.run([*compose,'-f',cf,'exec','-T','kafka','sh','-lc',command],capture_output=True,text=True,check=False,timeout=30)
def state(): return json.loads((root/'state.json').read_text())
def write(value): (root/'state.json').write_text(json.dumps(value,indent=2)+'\n')

write({'mode':'paused'}); time.sleep(2); exec_broker("timeout 10 /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --delete --group opsbench-group >/dev/null 2>&1 || true"); exec_broker("timeout 10 /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic opsbench-events >/dev/null 2>&1 || true"); time.sleep(2); exec_broker("timeout 15 /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --create --topic opsbench-events --partitions 1 --replication-factor 1 >/dev/null 2>&1 || true"); write({'mode':'baseline'}); time.sleep(20)
