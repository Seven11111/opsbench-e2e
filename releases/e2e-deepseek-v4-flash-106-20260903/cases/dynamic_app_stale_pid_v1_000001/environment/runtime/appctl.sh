#!/bin/sh
set -eu

PID_FILE=/run/demo-app.pid
LOG_FILE=/var/log/demo/app-process.log

# Reconciliation and an operator may request a restart at the same time. Keep
# PID-file transitions atomic without leaving a long-lived ``flock`` process
# behind in the container entrypoint.  The previous ``flock 9`` form acquired
# a descriptor lock but did not terminate on all util-linux versions, so the
# entrypoint remained inside ``appctl start`` and later controls observed a
# healthy port with a dead/stale PID record.
LOCK_DIR=/run/demo-appctl.lock.d
acquire_lock() {
  i=0
  while ! mkdir "$LOCK_DIR" 2>/dev/null; do
    i=$((i + 1))
    [ "$i" -lt 100 ] || return 1
    sleep 0.05
  done
  trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT INT TERM
}
acquire_lock

start() {
  if [ -e "$PID_FILE" ]; then
    echo "refusing to start: pid file already exists: $PID_FILE" >&2
    return 1
  fi
  set -a
  [ ! -f /etc/opsbench/app.env ] || . /etc/opsbench/app.env
  set +a
  port=${APP_PORT:-$(python3 -c 'import json; print(json.load(open("/etc/opsbench/app.json"))["port"])')}
  nohup sh -c 'exec 9>&-; ulimit -n 64; exec setpriv --reuid=demo --regid=demo --init-groups \
    python3 /opt/opsbench/runtime/app.pyc' >>"$LOG_FILE" 2>&1 &
  echo "$!" >"$PID_FILE"
  pid=$(cat "$PID_FILE")
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
    kill -0 "$pid" 2>/dev/null || return 1
    curl -fsS --max-time 1 "http://127.0.0.1:$port/health" >/dev/null 2>&1 && return 0
    sleep 0.1
  done
  return 1
}

stop() {
  if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    kill "$pid" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.1
    done
    kill -9 "$pid" 2>/dev/null || true
    rm -f "$PID_FILE"
  fi
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status)
    test -f "$PID_FILE" && kill -0 "$(cat "$PID_FILE")"
    ;;
  *) echo "usage: appctl start|stop|restart|status" >&2; exit 2 ;;
esac
