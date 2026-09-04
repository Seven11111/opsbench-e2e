# Elevated header rejection rate

Nginx error logs show 'upstream sent too big header' messages
Monitoring dashboard reports spike in header buffer rejection count

## Objective

Restore healthy header buffer rejection baseline

## Success Criteria

- The declared business operation returns HTTP 200.
- The header buffer rejections reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
