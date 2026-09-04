
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

slot_command='PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c "SELECT slot_name,restart_lsn,pg_current_wal_lsn() FROM pg_replication_slots WHERE slot_name LIKE '+chr(39)+'opsbench_%'+chr(39)+'"'
slots=ex(slot_command)
retained=float(native_state.get('pg_wal_lsn_diff','0') or 0); second_retained=float(second_state.get('pg_wal_lsn_diff','0') or 0)
injection_ok='pg_replication_slots' in native_state and 'pg_create_physical_replication_slot' in native_state
diagnostic_ok=slots.returncode==0 and 'restart_lsn' in slots.stdout and 'pg_current_wal_lsn' in slots.stdout
recovery_ok=http_ok('http://target:8080/business') and retained<=100000 and 'pg_replication_slots' in str(native_state)
persistence_ok=http_ok('http://target:8080/business') and second_retained<=100000 and second_state.get('pg_replication_slots') is not None

checks=[{"name":"business_operation","passed":http_ok('http://target:8080/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
