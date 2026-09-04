# Consumer commit success rate degraded

Commit success rate dropped below 50% over the last 5 minutes.
Offset commit requests are failing with ExceededThreshold error.

## Objective

Restore consumer commit success rate to healthy baseline.

## Success Criteria

- The declared business operation returns HTTP 200.
- The commit success rate reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
