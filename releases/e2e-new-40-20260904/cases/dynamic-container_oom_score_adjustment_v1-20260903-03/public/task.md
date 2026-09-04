# Elevated OOM Score in Container

Container's OOM score is above the healthy threshold.
HTTP requests to the service fail with 503 errors.

## Objective

Reduce OOM score to baseline and restore HTTP 200 responses.

## Success Criteria

- The declared business operation returns HTTP 200.
- The oom score reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
