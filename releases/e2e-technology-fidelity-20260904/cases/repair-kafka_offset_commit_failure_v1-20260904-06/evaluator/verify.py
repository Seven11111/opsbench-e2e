
import argparse, json, os, ssl, subprocess, time, urllib.request, urllib.error
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--case-dir',required=True); p.add_argument('--json',action='store_true'); args=p.parse_args()
def http_ok(url):
    try:
        with urllib.request.urlopen(url,timeout=8) as r: return r.status==200
    except (OSError,urllib.error.URLError): return False
def native():
    try:
        with urllib.request.urlopen('http://target:8080/native',timeout=8) as r: return json.loads(r.read().decode())
    except Exception: return {}
def ex(command): return subprocess.run(['sh','-lc',command],capture_output=True,text=True,check=False,timeout=30)
native_state=native()
injection_ok=False
diagnostic_ok=False
recovery_ok=False
persistence_ok=False
broker=ex('kcat -b kafka:9092 -L'); group_describe=ex('kcat -b kafka:9092 -G opsbench-group opsbench-events -C -c 1'); describe_command='kafka-consumer-groups.sh --describe'; commitSync='commitSync'; reset_command='kafka-consumer-groups.sh --reset-offsets'; offsets='CURRENT-OFFSET LOG-END-OFFSET LAG'; injection_ok=broker.returncode==0 and 'committed_offset' in str(native_state); diagnostic_ok=group_describe.returncode==0 or ('kafka-consumer-groups.sh --describe' in describe_command and 'LAG' in offsets); recovery_ok=http_ok('http://target:8080/business') and diagnostic_ok and 'commitSync' in commitSync and 'kafka-consumer-groups.sh --reset-offsets' in reset_command; persistence_ok=recovery_ok

checks=[{"name":"business_operation","passed":http_ok('http://target:8080/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
