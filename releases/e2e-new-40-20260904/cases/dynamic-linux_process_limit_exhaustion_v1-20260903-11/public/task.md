# Process creation failures

User applications fail to spawn new processes. System logs show 'resource temporarily unavailable' errors.

## Objective

Restore process creation capability.

## Success Criteria

- The declared business operation returns HTTP 200.
- The process limit headroom reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
