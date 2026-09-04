
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

queue=native_state
queue_probe=ex("curl --noproxy '*' -fsS -u opsbench:opsbench-local-only http://rabbitmq:15672/api/queues/%2F/opsbench-ack")
channel_command='python -c '+chr(34)+'import pika; c=pika.BlockingConnection(pika.ConnectionParameters('+chr(39)+'rabbitmq'+chr(39)+')); ch=c.channel(); ch.queue_declare(queue='+chr(39)+'opsbench-ack'+chr(39)+',durable=True); ch.close(); c.close()'+chr(34)
channel_probe=ex(channel_command)
unacked=int(queue.get('messages_unacknowledged',-1)); ready=int(queue.get('messages_ready',-1))
second_unacked=int(second_state.get('messages_unacknowledged',-1)); second_ready=int(second_state.get('messages_ready',-1))
ack_probe=queue.get('basic_ack')
injection_ok=queue_probe.returncode==0 and int(queue.get('deliveries',0))>=0 and queue.get('consumer_timeout') is not None
diagnostic_ok=queue_probe.returncode==0 and channel_probe.returncode==0 and 'messages_unacknowledged' in queue and 'consumers' in queue
recovery_ok=http_ok('http://target:8080/business') and unacked==0 and ready==0 and int(ack_probe or 0)>=1
persistence_ok=http_ok('http://target:8080/business') and second_unacked==0 and second_ready==0 and int(second_state.get('consumers',-1))>0

checks=[{"name":"business_operation","passed":http_ok('http://target:8080/business'),"weight":0.2},{"name":"injection_evidence","passed":injection_ok,"weight":0.2},{"name":"diagnostic_evidence","passed":diagnostic_ok,"weight":0.2},{"name":"recovery_evidence","passed":recovery_ok,"weight":0.2},{"name":"persistence","passed":persistence_ok,"weight":0.2}]
for item in checks: item['detail']=str(native_state)[:1000]
result={"passed":all(bool(item['passed']) for item in checks),"score":round(sum(item['weight'] for item in checks if item['passed']),6),"checks":checks}
print(json.dumps(result)); raise SystemExit(0 if result['passed'] else 1)
