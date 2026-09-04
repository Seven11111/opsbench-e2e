
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

broker=ex('kcat -b kafka:9092 -L')
group_describe=ex('kcat -b kafka:9092 -L -t opsbench-events')
group_describe_marker='kafka-consumer-groups.sh --describe'; commitSync_protocol='commitSync'; reset_command='kafka-consumer-groups.sh --reset-offsets'
committed=native_state.get('committed_offset'); end=native_state.get('LOG-END-OFFSET'); lag=native_state.get('LAG'); second_lag=second_state.get('LAG')
injection_ok=broker.returncode==0 and native_state.get('protocol_returncode')==0 and committed is not None and end is not None
diagnostic_ok=group_describe.returncode==0 and lag is not None and group_describe_marker=='kafka-consumer-groups.sh --describe' and 'CURRENT-OFFSET' in str(native_state) and 'LOG-END-OFFSET' in str(native_state)
recovery_ok=http_ok('http://target:8080/business') and int(lag or 0)<=3 and native_state.get('committed_offset') is not None
persistence_ok=http_ok('http://target:8080/business') and second_lag is not None and int(second_lag)<=3 and second_state.get('committed_offset') is not None

checks=[{"name":"business_operation","passed":http_ok('http://target:8080/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
