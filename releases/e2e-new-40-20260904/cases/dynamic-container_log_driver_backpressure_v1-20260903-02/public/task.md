# Elevated log delivery lag

Log delivery lag is consistently above 10 seconds.
Container logs are delayed or missing.

## Objective

Reduce log delivery lag to a healthy baseline under 2 seconds.

## Success Criteria

- The declared business operation returns HTTP 200.
- The log delivery lag reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
