# Inconsistent image pull behavior

Container logs show repeated image pulls on every restart despite local image existing.
Service health checks fail after restart due to unexpected image version mismatch.

## Objective

Restore the configured image pull policy to prevent unnecessary image refreshes.

## Success Criteria

- The declared business operation returns HTTP 200.
- The image policy reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
