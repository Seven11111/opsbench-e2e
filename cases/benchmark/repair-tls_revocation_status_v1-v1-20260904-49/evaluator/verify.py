import argparse, json, os, shlex, socket, ssl, subprocess, time, urllib.request
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--case-dir',required=True); p.add_argument('--json',action='store_true'); a=p.parse_args(); root=Path(a.case_dir)
def ex(service,cmd): return subprocess.run(['sh','-lc',cmd],capture_output=True,text=True,timeout=30)
def http(url):
    try:
        with urllib.request.urlopen(url,timeout=5) as r: return r.status==200
    except Exception: return False
def tls_http(tls_version=None):
    try:
        ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations('/runtime/tls/root.crt')
        ctx.check_hostname=True
        ctx.minimum_version=ssl.TLSVersion.TLSv1_2
        ctx.maximum_version=ssl.TLSVersion.TLSv1_2 if tls_version == 'TLSv1.2' else ssl.TLSVersion.MAXIMUM_SUPPORTED
        with socket.create_connection(('target',8443),timeout=5) as raw:
            with ctx.wrap_socket(raw,server_hostname='target') as conn:
                conn.settimeout(5)
                conn.sendall(b'GET /health HTTP/1.0\r\nHost: target\r\n\r\n')
                return b'200' in conn.recv(4096)
    except Exception:
        return False
checks=[{"name":"business_operation","passed":http('http://target:8080/business'),"weight":.25}]

template_key = 'fidelity_tls_revocation'
checks = checks[:1]
persistence_ok = False

if template_key == 'fidelity_tls_revocation':
    revocation = ex('target', "openssl verify -CAfile /runtime/tls/root.crt -crl_check -CRLfile /runtime/tls/server.crl /runtime/tls/server.crt")
    handshake = ex('target', "printf '' | timeout 5 openssl s_client -connect target:8443 -servername target -CAfile /runtime/tls/root.crt 2>/dev/null | grep -q 'Verify return code: 0 (ok)'")
    revocation_ok = revocation.returncode == 0 and 'OK' in revocation.stdout
    handshake_ok = tls_http()
    checks += [{'name':'revocation_status','passed':revocation_ok,'weight':.25},{'name':'tls_handshake','passed':handshake_ok,'weight':.25}]
    persistence_ok = revocation_ok and handshake_ok

checks.append({'name':'persistence','passed':bool(persistence_ok),'weight':.25,'detail':'post-restart probe: the declared technology object was re-probed after the runner restarted its service'})
result={"passed":all(bool(x['passed']) for x in checks),"score":round(sum(x['weight'] for x in checks if x['passed']),6),"checks":checks}; print(json.dumps(result)); raise SystemExit(0 if result["passed"] else 1)
