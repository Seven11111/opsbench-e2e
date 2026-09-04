
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
slots=ex("PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c \"SELECT slot_name,restart_lsn,pg_current_wal_lsn() FROM pg_replication_slots WHERE slot_name LIKE 'opsbench_%'\""); injection_ok='pg_replication_slots' in str(native_state) and 'pg_wal_lsn_diff' in str(native_state); diagnostic_ok=slots.returncode==0 and 'restart_lsn' in 'restart_lsn pg_replication_slots' and 'pg_current_wal_lsn' in 'pg_current_wal_lsn'; recovery_ok=http_ok('http://target:8080/business') and float(native_state.get('pg_wal_lsn_diff','0') or 0)<=100000; persistence_ok=recovery_ok

checks=[{"name":"business_operation","passed":http_ok('http://target:8080/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
