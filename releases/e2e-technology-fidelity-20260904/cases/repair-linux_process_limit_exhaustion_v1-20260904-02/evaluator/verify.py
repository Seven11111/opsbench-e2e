
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

current=int(native_state.get('pids.current',0)); maximum=int(native_state.get('pids.max',0))
second_current=int(second_state.get('pids.current',0)); second_maximum=int(second_state.get('pids.max',0))
creation_signal=native_state.get('process creation'); waitpid_recovery=second_state.get('child_processes'); terminate_recovery=second_state.get('process_creation')
injection_ok=maximum>0 and current>=0 and native_state.get('process_creation') in {'EAGAIN','available'}
diagnostic_ok=maximum>=current and 'pids.current' in native_state and 'pids.max' in native_state and creation_signal in {'EAGAIN','available'}
recovery_ok=http_ok('http://target:8080/business') and native_state.get('process_creation')=='available'
persistence_ok=http_ok('http://target:8080/business') and second_maximum>0 and second_current<second_maximum and waitpid_recovery==0 and terminate_recovery=='available'

checks=[{"name":"business_operation","passed":http_ok('http://target:8080/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
