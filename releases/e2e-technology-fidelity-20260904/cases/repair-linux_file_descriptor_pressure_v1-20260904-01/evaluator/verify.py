
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

fd=int(native_state.get('fd_count',0)); soft=int(native_state.get('fd_soft_limit',0)); headroom=int(native_state.get('fd_headroom',0))
second_fd=int(second_state.get('fd_count',0)); second_soft=int(second_state.get('fd_soft_limit',0)); second_headroom=int(second_state.get('fd_headroom',0))
procfs_root=native_state.get('procfs'); procfs_contract='/proc/self/fd'; nofile_limit=native_state.get('RLIMIT_NOFILE'); close_probe=second_state.get('fd_headroom')
injection_ok=soft>0 and fd>=0 and native_state.get('open_probe_errno') in {'EMFILE','available','not-probed'}
persistence_fd_table=second_state.get('procfs')
diagnostic_ok=fd<=soft and headroom>=0 and bool(native_state.get('readlink')) and procfs_root is not None and procfs_root.startswith('/proc') and nofile_limit==soft
recovery_ok=http_ok('http://target:8080/business') and headroom>60 and close_probe is not None
persistence_ok=http_ok('http://target:8080/business') and second_soft>0 and second_fd<=second_soft and second_headroom>60

checks=[{"name":"business_operation","passed":http_ok('http://target:8080/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
