
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

targets=ex("curl --noproxy '*' -fsS http://prometheus:9090/api/v1/targets?state=active")
config=ex("curl --noproxy '*' -fsS http://prometheus:9090/api/v1/status/config")
payload=json.loads(targets.stdout)
active=next((item for item in payload.get('data',{}).get('activeTargets',[]) if item.get('labels',{}).get('job')=='opsbench-target'),{})
target_health=active.get('health'); last_error=str(active.get('lastError') or ''); scrape_interval_value=second_state.get('scrape_interval'); health_label='health='+str(target_health)
injection_ok=targets.returncode==0 and 'lastError' in targets.stdout and 'scrape_timeout' in config.stdout
diagnostic_ok=targets.returncode==0 and config.returncode==0 and active.get('labels',{}).get('job')=='opsbench-target' and 'scrapeDuration' in targets.stdout and scrape_interval_value is not None
recovery_ok=http_ok('http://target:8080/business') and health_label=='health=up' and not last_error
persistence_ok=http_ok('http://target:8080/business') and second_state.get('health')=='up' and not str(second_state.get('lastError') or '')

checks=[{"name":"business_operation","passed":http_ok('http://target:8080/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
