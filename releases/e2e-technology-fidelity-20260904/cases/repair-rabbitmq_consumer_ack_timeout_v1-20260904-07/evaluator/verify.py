
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
queue=native_state; queue_probe=ex("curl --noproxy '*' -fsS -u opsbench:opsbench-local-only http://rabbitmq:15672/api/queues/%2F/opsbench-ack"); channel_probe=ex("python -c 'import pika; c=pika.BlockingConnection(pika.ConnectionParameters(\"rabbitmq\")); channel=c.channel(); channel.close(); c.close()'"); injection_ok='messages_unacknowledged' in queue and 'basic_ack' in str(queue); diagnostic_ok=queue_probe.returncode==0 and channel_probe.returncode==0 and 'consumer_timeout' in str(queue) and 'consumers' in queue; recovery_ok=http_ok('http://target:8080/business') and 'messages_ready' in str(queue) and int(queue.get('messages_unacknowledged',0) or 0)==0; persistence_ok=recovery_ok

checks=[{"name":"business_operation","passed":http_ok('http://target:8080/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
