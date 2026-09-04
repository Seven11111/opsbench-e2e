import json, os, shlex, subprocess, sys, time, urllib.request
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--case-dir')+1]).resolve(); runtime=Path('/runtime') if Path('/runtime').is_dir() else root/'environment/runtime'
def target(command): return subprocess.run(['/bin/sh','-lc',command],capture_output=True,text=True,timeout=30)
def write(value): (runtime/'fault.json').write_text(json.dumps(value)+'\n')
def psql(sql): return target('PGPASSWORD=opsbench-local-only psql -v ON_ERROR_STOP=1 -h db -U opsbench -d app -At -c '+shlex.quote(sql))
def redis(args): return target('redis-cli -h redis '+args)
def api(path,method='GET',data=b''):
 import base64
 req=urllib.request.Request('http://rabbitmq:15672'+path,method=method,data=data); req.add_header('Authorization','Basic '+base64.b64encode(b'opsbench:opsbench-local-only').decode()); req.add_header('Content-Type','application/json')
 try:
  with urllib.request.urlopen(req,timeout=10) as r: return r.status,r.read().decode()
 except Exception as exc: return 0,str(exc)
r=psql("SELECT COALESCE(pg_wal_lsn_diff(pg_current_wal_lsn(),restart_lsn),0) FROM pg_replication_slots WHERE slot_name='opsbench_hold';")
if r.returncode or not any(float(x or 0)>100000 for x in r.stdout.split()): raise SystemExit('WAL retention signal not observed')
