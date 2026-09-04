# Healthcheck not responding

Healthcheck endpoint returns HTTP 503 errors.
Healthcheck interval is irregular and exceeds expected timeout.

## Objective

Restore healthcheck to respond correctly within normal interval.

## Success Criteria

- The declared business operation returns HTTP 200.
- The healthcheck interval reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
