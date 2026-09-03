#!/bin/sh
case "$1" in status) curl -fsS http://127.0.0.1:8080/health >/dev/null;; start|stop) exit 0;; restart) curl -fsS -X POST -H 'Content-Type: application/json' -d '{"action":"restore"}' http://127.0.0.1:8080/opsbench/control >/dev/null;; *) exit 2;; esac
