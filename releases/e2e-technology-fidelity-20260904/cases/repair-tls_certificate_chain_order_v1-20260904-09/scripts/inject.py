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
p=runtime/'tls/server.fullchain.crt'; certificates=p.read_text().split('-----END CERTIFICATE-----'); certificates=[item+'-----END CERTIFICATE-----\n' for item in certificates if 'BEGIN CERTIFICATE' in item]; p.write_text(''.join(reversed(certificates))); openssl_verify=subprocess.run(['sh','-lc',f'openssl verify -CAfile {runtime}/tls/root.crt {p}'],capture_output=True,text=True,check=False); identity=subprocess.run(['openssl','x509','-in',str(runtime/'tls/api.crt'),'-noout','-issuer','-subject'],capture_output=True,text=True,check=False); issuer=identity.stdout; subject=identity.stdout; reload_target(); time.sleep(1)
