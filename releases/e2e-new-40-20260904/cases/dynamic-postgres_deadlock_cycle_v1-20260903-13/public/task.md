# Elevated deadlock waiters

Deadlock waiters count consistently exceeds threshold.
Business operations return HTTP 503 errors.

## Objective

Reduce deadlock waiters to healthy baseline.

## Success Criteria

- The declared business operation returns HTTP 200.
- The deadlock waiters reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
