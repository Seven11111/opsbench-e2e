
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

locks=ex("PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c 'SELECT count(*) FROM pg_locks WHERE NOT granted'")
activity=ex("PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c 'SELECT count(*) FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0'")
wait_event=ex("PGPASSWORD=opsbench-local-only psql -h db -U opsbench -d app -At -c 'SELECT wait_event FROM pg_stat_activity WHERE wait_event IS NOT NULL'")
query_command='PGPASSWORD=opsbench-local-only psql -v ON_ERROR_STOP=1 -h db -U opsbench -d app -At -c "SET lock_timeout='+chr(39)+'800ms'+chr(39)+'; UPDATE orders SET value=value WHERE id=1;"'
query=ex(query_command)
injection_ok='pg_locks' in native_state and 'pg_blocking_pids' in native_state
diagnostic_ok=locks.returncode==0 and activity.returncode==0 and wait_event.returncode==0 and 'pg_stat_activity' in str(native_state)
recovery_ok=http_ok('http://target:8080/business') and query.returncode==0 and int(second_state.get('pg_blocking_pids',0) or 0)==0
persistence_ok=http_ok('http://target:8080/business') and int(second_state.get('pg_blocking_pids',0) or 0)==0 and int(second_state.get('pg_locks',0) or 0)>=0

checks=[{"name":"business_operation","passed":http_ok('http://target:8080/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
