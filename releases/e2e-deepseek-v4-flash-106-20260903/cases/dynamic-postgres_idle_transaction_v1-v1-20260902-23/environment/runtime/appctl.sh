#!/bin/sh
case "$1" in
  status) exec curl -fsS http://127.0.0.1:8080/health >/dev/null ;;
  start|stop|restart) exit 0 ;;
  *) exit 2 ;;
esac
