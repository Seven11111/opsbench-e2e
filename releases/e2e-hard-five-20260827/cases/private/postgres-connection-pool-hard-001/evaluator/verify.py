import argparse, json, os, shlex, subprocess, urllib.request
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--case-dir',required=True); p.add_argument('--json',action='store_true'); a=p.parse_args(); root=Path(a.case_dir)
state=json.loads((root/'environment/runtime/state.json').read_text()); compose=shlex.split(os.environ.get('OPSBENCH_COMPOSE_BIN','docker-compose')); cf=str(root/'environment/docker-compose.yaml')
def target(command): return subprocess.run([*compose,'-f',cf,'exec','-T','target','sh','-lc',command],capture_output=True,text=True,check=False)
def broker(command): return subprocess.run([*compose,'-f',cf,'exec','-T','kafka','sh','-lc',command],capture_output=True,text=True,check=False)
checks=[]
def valid_cache(value):
    try:
        payload=json.loads(value)
        return payload.get('version')==1 and isinstance(payload.get('items'),list)
    except Exception:
        return False
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
    with opener.open('http://127.0.0.1:18086/health',timeout=4) as r: health=r.status==200
except Exception: health=False
try:
    with opener.open('http://127.0.0.1:18086/query',timeout=5) as r: business=r.status==200
except Exception: business=False
checks.append({'name':'service_health','passed':health,'weight':.2,'detail':'live health endpoint'})
checks.append({'name':'business_operation','passed':business,'weight':.2,'detail':'live business endpoint'})
r=target("PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT count(*) FROM pg_stat_activity WHERE application_name='opsbench-pool-holder';\""); checks.append({'name':'pool_holders_absent','passed':r.returncode==0 and r.stdout.strip()=='0','weight':.2,'detail':r.stdout.strip()})
checks.append({'name':'persistence','passed':state.get('mode')=='baseline','weight':.2,'detail':str(state)})
passed=all(x['passed'] for x in checks); score=sum(x['weight'] for x in checks if x['passed']); print(json.dumps({'passed':passed,'score':round(score,6),'checks':checks})); raise SystemExit(0 if passed else 1)
