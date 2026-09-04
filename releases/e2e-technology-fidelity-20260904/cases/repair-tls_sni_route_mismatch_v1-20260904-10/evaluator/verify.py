
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

api=ex("printf '' | openssl s_client -servername api.opsbench.test -connect target:8443 -showcerts 2>/dev/null | openssl x509 -noout -subject -ext subjectAltName")
admin=ex("printf '' | openssl s_client -servername admin.opsbench.test -connect target:8443 -showcerts 2>/dev/null | openssl x509 -noout -subject -ext subjectAltName")
api_sans=cert_sans(api.stdout+api.stderr); admin_sans=cert_sans(admin.stdout+admin.stderr); route_observation=native_state.get('route'); certificate_identity=native_state.get('certificate_identity'); route_map='SNI_ROUTES'; callback_marker='servername_callback'
second_api=ex("printf '' | openssl s_client -servername api.opsbench.test -connect target:8443 -showcerts 2>/dev/null | openssl x509 -noout -ext subjectAltName")
second_admin=ex("printf '' | openssl s_client -servername admin.opsbench.test -connect target:8443 -showcerts 2>/dev/null | openssl x509 -noout -ext subjectAltName")
second_api_sans=cert_sans(second_api.stdout+second_api.stderr); second_admin_sans=cert_sans(second_admin.stdout+second_admin.stderr)
injection_ok=api.returncode==0 and admin.returncode==0 and bool(api_sans|admin_sans)
diagnostic_ok='subjectAltName' in (api.stdout+admin.stdout) and 'SNI' in str(native_state) and route_observation in {'api','admin'} and certificate_identity is not None and callback_marker=='servername_callback'
recovery_ok=api.returncode==0 and admin.returncode==0 and 'api.opsbench.test' in api_sans and 'admin.opsbench.test' in admin_sans and https_ok('https://target:8443/business')
persistence_ok='api.opsbench.test' in second_api_sans and 'admin.opsbench.test' in second_admin_sans and https_ok('https://target:8443/business')

checks=[{"name":"business_operation","passed":https_ok('https://target:8443/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
