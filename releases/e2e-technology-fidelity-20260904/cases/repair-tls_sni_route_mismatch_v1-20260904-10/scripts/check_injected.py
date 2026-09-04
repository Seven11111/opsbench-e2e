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
def sans(name):
 r=subprocess.run(['sh','-lc',f"printf '' | openssl s_client -connect 127.0.0.1:8443 -servername {name} -showcerts 2>/dev/null | openssl x509 -noout -ext subjectAltName"],capture_output=True,text=True,check=False); return r, r.stdout+r.stderr
api_result,api=sans('api.opsbench.test'); admin_result,admin=sans('admin.opsbench.test')
if api_result.returncode != 0 or admin_result.returncode != 0 or 'DNS:admin.opsbench.test' not in api or 'DNS:api.opsbench.test' not in admin: raise SystemExit('native TLS SNI certificate identities did not demonstrate the swapped route')
