
import argparse, json, re, ssl, subprocess, time, urllib.error, urllib.request
p=argparse.ArgumentParser(); p.add_argument('--case-dir',required=True); p.add_argument('--json',action='store_true'); args=p.parse_args()
def http_ok(url):
    try:
        with urllib.request.urlopen(url,timeout=8) as response: return response.status==200
    except (OSError,urllib.error.URLError): return False
def https_ok(url):
    try:
        context=ssl.create_default_context(cafile='/runtime/tls/root.crt'); context.check_hostname=False
        with urllib.request.urlopen(url,context=context,timeout=8) as response: return response.status==200
    except (OSError,urllib.error.URLError,ssl.SSLError): return False
def native():
    try:
        with urllib.request.urlopen('http://target:8080/native',timeout=8) as response: return json.loads(response.read().decode())
    except Exception: return {}
def ex(command): return subprocess.run(['sh','-lc',command],capture_output=True,text=True,check=False,timeout=30)
def cert_sans(value): return set(re.findall(r'DNS:([A-Za-z0-9_.-]+)',value))
native_state=native()
# The host runner has completed the declared lifecycle boundary.
lifecycle_boundary='post-restart lifecycle boundary'
time.sleep(0.2)
second_state=native()
injection_ok=False
diagnostic_ok=False
recovery_ok=False
persistence_ok=False

verify=ex("openssl verify -show_chain -CAfile /runtime/tls/root.crt /runtime/tls/server.fullchain.crt")
handshake=ex("printf '' | openssl s_client -connect target:8443 -servername api.opsbench.test -showcerts 2>/dev/null")
context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT); context.check_hostname=False
injection_ok=native_state.get('verify_returncode') in {0,1} and 'certificate_chain' in native_state
diagnostic_ok=verify.returncode==0 and 'issuer' in str(native_state) and 'subject' in str(native_state) and 'certificate_chain' in str(native_state) and isinstance(context,ssl.SSLContext)
recovery_ok=verify.returncode==0 and handshake.returncode==0 and https_ok('https://target:8443/business')
persistence_ok=int(second_state.get('verify_returncode',1))==0 and https_ok('https://target:8443/business')

checks=[{"name":"business_operation","passed":https_ok('https://target:8443/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
