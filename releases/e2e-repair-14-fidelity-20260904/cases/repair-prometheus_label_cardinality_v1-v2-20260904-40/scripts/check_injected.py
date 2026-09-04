import json, os, shlex, subprocess, sys, time, urllib.request
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--case-dir')+1]).resolve(); runtime=Path('/runtime') if Path('/runtime').is_dir() else root/'environment/runtime'
def target(command): return subprocess.run(['/bin/sh','-lc',command],capture_output=True,text=True,timeout=30)
def write(value): (runtime/'fault.json').write_text(json.dumps(value)+'\n')
def control(action):
 req=urllib.request.Request('http://target:8080/opsbench/control',method='POST',data=json.dumps({'action':action}).encode(),headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=10) as r: return r.status
def psql(sql): return target('PGPASSWORD=opsbench-local-only psql -v ON_ERROR_STOP=1 -h db -U opsbench -d app -At -c '+shlex.quote(sql))
def redis(args): return target('redis-cli -h redis '+args)
def api(path,method='GET',data=b''):
 import base64
 req=urllib.request.Request('http://rabbitmq:15672'+path,method=method,data=data); req.add_header('Authorization','Basic '+base64.b64encode(b'opsbench:opsbench-local-only').decode()); req.add_header('Content-Type','application/json')
 try:
  with urllib.request.urlopen(req,timeout=10) as r: return r.status,r.read().decode()
 except Exception as exc: return 0,str(exc)
time.sleep(3); r=urllib.request.urlopen('http://prometheus:9090/api/v1/query?query=count%28opsbench_request_total%29',timeout=5); payload=json.loads(r.read().decode()); value=float(payload['data']['result'][0]['value'][1]);
if r.status!=200 or value < 100: raise SystemExit('Prometheus high-cardinality signal not observed')
