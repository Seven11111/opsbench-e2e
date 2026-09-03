import json, os, subprocess, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer
def read(): return json.load(open('/runtime/state.json'))
consumer=None
last_mode=None
def loop():
    global consumer, last_mode
    while True:
        mode=read().get('mode')
        if mode == 'baseline' and (consumer is None or consumer.poll() is not None):
            if consumer is not None:
                try:
                    consumer.wait(timeout=2)
                except Exception:
                    consumer.kill()
                    consumer.wait(timeout=2)
            consumer=subprocess.Popen(['kcat','-b','kafka:9092','-G','opsbench-group','-X','enable.auto.commit=true','-X','auto.commit.interval.ms=100','-X','auto.offset.reset=earliest','opsbench-events'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if last_mode != 'baseline':
                subprocess.run("printf '%s\n' bootstrap | kcat -b kafka:9092 -t opsbench-events -P", shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if mode != 'baseline' and consumer is not None:
            consumer.kill()
            try:
                consumer.wait(timeout=2)
            except Exception:
                consumer.kill()
                consumer.wait(timeout=2)
            consumer=None
        if mode == 'paused' and not read().get('producer_paused'):
            subprocess.run("printf '%s\n' event | kcat -b kafka:9092 -t opsbench-events -P", shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        last_mode=mode
        time.sleep(.5)
threading.Thread(target=loop,daemon=True).start()
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        s=read(); ok=self.path=='/health' or (self.path=='/lag' and s.get('mode')=='baseline')
        self.send_response(200 if ok else 503); self.end_headers(); self.wfile.write(json.dumps(s).encode())
    def log_message(self,*a): pass
HTTPServer(('0.0.0.0',18088),H).serve_forever()
