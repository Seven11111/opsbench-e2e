import argparse, json, os, shlex, subprocess, tempfile, urllib.request
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--case-dir',required=True); p.add_argument('--json',action='store_true'); a=p.parse_args(); root=Path(a.case_dir)
state=json.loads((root/'environment/runtime/state.json').read_text()); compose=shlex.split(os.environ.get('OPSBENCH_COMPOSE_BIN','docker-compose')); cf=str(root/'environment/docker-compose.yaml')
def _exec(service, command):
    argv=[*compose,'-f',cf,'exec','-T',service,'sh','-lc',command]
    with tempfile.TemporaryDirectory(prefix='opsbench-verifier-') as td:
        stdout_path=os.path.join(td,'stdout.log'); stderr_path=os.path.join(td,'stderr.log')
        with open(stdout_path,'wb') as stdout_file, open(stderr_path,'wb') as stderr_file:
            process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=stdout_file,stderr=stderr_file)
            try:
                returncode=process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                if os.name=='nt':
                    subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,check=False,timeout=5)
                else:
                    process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
                returncode=124
        stdout=open(stdout_path,'rb').read().decode('utf-8','replace') if os.path.exists(stdout_path) else ''
        stderr=open(stderr_path,'rb').read().decode('utf-8','replace') if os.path.exists(stderr_path) else ''
    if returncode==124:
        stderr='command timed out after 20s\n'+stderr
    return subprocess.CompletedProcess(argv,returncode,stdout=stdout,stderr=stderr)
def target(command): return _exec('target',command)
def broker(command): return _exec('kafka',command)
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
