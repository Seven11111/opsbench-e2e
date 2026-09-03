from __future__ import annotations
import http.server, json, os, signal, threading, time
from pathlib import Path

ROOT = Path("/runtime")
PROFILE = Path("/etc/opsbench/profile.json")
FAULT = ROOT / "fault.json"
STATUS = ROOT / "status.json"
LOCK = threading.Lock()
STATE = {}

def read(path, default):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else dict(default)
    except (OSError, ValueError):
        return dict(default)

def reconcile():
    global STATE
    profile = read(PROFILE, {})
    fault = read(FAULT, {"mode": "baseline"})
    mode = str(fault.get("mode") or "baseline")
    active = mode not in {"baseline", "repaired"}
    signal_name = str(profile.get("signal") or "operational_signal")
    variant = str(profile.get("variant") or "v1")
    signal_value = 2 if active and variant == "v2" else (1 if active else 0)
    # Every profile has a different observable counter.  This is the runtime
    # capability boundary; the public task only names the resulting signal.
    values = {
        "watch_headroom": 0 if active else 100,
        "port_headroom": 0 if active else 128,
        "zombie_count": 3 if active else 0,
        "throttled_usec": 100000 if active else 0,
        "tmpfs_free_bytes": 0 if active else 1048576,
        "capability_probe": 1 if active else 0,
        "dependency_ready": 0 if active else 1,
        "shutdown_completion": 0 if active else 1,
        "workdir_probe": 0 if active else 1,
        "redirect_hops": 6 if active else 1,
        "header_rejections": 2 if active else 0,
        "decode_errors": 2 if active else 0,
        "chain_depth": 1 if active else 2,
        "protocol_overlap": 0 if active else 1,
        "revocation_status": 0 if active else 1,
        "dead_tuple_ratio": 90 if active else 2,
        "wal_retained_bytes": 1048576 if active else 0,
        "auth_policy_result": 0 if active else 1,
        "sequence_headroom": 0 if active else 1000,
        "under_replicated_partitions": 1 if active else 0,
        "rebalance_rate": 8 if active else 0,
        "unacked_messages": 8 if active else 0,
        "evicted_keys": 12 if active else 0,
        "series_headroom": 0 if active else 100,
        "parse_errors": 5 if active else 0,
    }
    STATE = {
        "healthy": not active, "fault_active": active, "mode": mode,
        "mechanism": profile.get("mechanism", "unknown"), "variant": variant,
        "mechanism_signal": signal_name, "signal_value": signal_value,
        "signal_reading": values.get(signal_name, signal_value),
        "resource_class": profile.get("resource"),
        "observability": profile.get("observability"),
        "repair_surface": profile.get("repair"),
        "repair_mode": str(fault.get("repair_mode") or ("persistent" if mode == "repaired" else "")),
        "updated_at": time.time(),
    }
    with LOCK:
        STATUS.write_text(json.dumps(STATE, sort_keys=True) + "\n", encoding="utf-8")

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def send_json(self, code, payload):
        body = json.dumps(payload, sort_keys=True).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        reconcile()
        if self.path == "/metrics":
            body = ("opsbench_fault_active %d\nopsbench_signal_value %d\nopsbench_%s %s\n" % (int(STATE["fault_active"]), int(STATE["signal_value"]), STATE["mechanism_signal"], STATE["signal_reading"])).encode()
            self.send_response(200); self.send_header("Content-Type", "text/plain"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if self.path in {"/health", "/business"}: self.send_json(200 if STATE["healthy"] else 503, {"healthy": STATE["healthy"], "operation": self.path[1:]}); return
        if self.path == "/opsbench/state": self.send_json(200, dict(STATE)); return
        self.send_json(404, {"error": "not_found"})
    def do_POST(self):
        if self.path != "/opsbench/control": self.send_json(404, {"error": "not_found"}); return
        length = int(self.headers.get("Content-Length", "0") or 0)
        try: payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, TypeError): payload = {}
        if str(payload.get("action") or "") not in {"restore", "restore_service_state", "repair_observed_fault"}:
            self.send_json(400, {"healthy": False, "error": "bounded restore is required"}); return
        FAULT.write_text(json.dumps({"mode": "repaired", "repair_mode": "persistent"}) + "\n", encoding="utf-8")
        reconcile(); self.send_json(200, {"healthy": True, "action": "restore"})

def main():
    FAULT.write_text(json.dumps({"mode": "baseline", "repair_mode": ""}) + "\n", encoding="utf-8")
    reconcile()
    server = http.server.ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    def refresh():
        while True: reconcile(); time.sleep(0.2)
    threading.Thread(target=refresh, daemon=True).start()
    def stop(*_): threading.Thread(target=server.shutdown, daemon=True).start()
    for sig in (signal.SIGTERM, signal.SIGINT): signal.signal(sig, stop)
    server.serve_forever()
if __name__ == "__main__": main()
