# Protected API 401 errors

Protected API endpoints return HTTP 401 Unauthorized
Token validity checks fail

## Objective

Recover token validity to a healthy baseline

## Success Criteria

- The declared business operation returns HTTP 200.
- The token validity reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
