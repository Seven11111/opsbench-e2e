# Keepalive connections returning HTTP 503 errors

Nginx logs show keepalive connections returning HTTP 503 errors.
Server memory usage is elevated above the normal baseline.

## Objective

Restore keepalive request reliability to normal levels.

## Success Criteria

- The declared business operation returns HTTP 200.
- The keepalive requests reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
