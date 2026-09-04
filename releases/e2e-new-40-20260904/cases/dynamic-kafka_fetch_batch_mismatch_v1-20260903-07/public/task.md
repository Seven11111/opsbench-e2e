# Rising fetch batch errors

Consumer logs show fetch batch errors increasing.
Offsets are reported as missing or out of range.

## Objective

Restore fetch batch processing to a healthy baseline.

## Success Criteria

- The declared business operation returns HTTP 200.
- The fetch batch errors reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
