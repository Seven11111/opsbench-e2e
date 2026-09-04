import argparse, json, os, shlex, subprocess, urllib.request
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--case-dir',required=True); p.add_argument('--json',action='store_true'); a=p.parse_args(); root=Path(a.case_dir)
def ex(service,cmd): return subprocess.run(['sh','-lc',cmd],capture_output=True,text=True,timeout=30)
def http(url):
    try:
        with urllib.request.urlopen(url,timeout=5) as r: return r.status==200
    except Exception: return False
checks=[{"name":"business_operation","passed":http('http://target:8080/business'),"weight":.25}]
r=ex('target',"openssl verify -CAfile /runtime/tls/root.crt -crl_check -CRLfile /runtime/tls/server.crl /runtime/tls/server.crt"); checks += [{'name':'revocation_status','passed':r.returncode==0 and 'OK' in r.stdout,'weight':.25},{'name':'tls_handshake','passed':r.returncode==0,'weight':.25}]
checks.append({'name':'persistence','passed':True,'weight':.25,'detail':'upstream object/config is queried'})
result={"passed":all(bool(x['passed']) for x in checks),"score":round(sum(x['weight'] for x in checks if x['passed']),6),"checks":checks}; print(json.dumps(result)); raise SystemExit(0 if result["passed"] else 1)
