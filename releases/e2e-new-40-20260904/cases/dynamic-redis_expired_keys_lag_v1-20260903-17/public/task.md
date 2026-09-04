# Stale cache entries not evicted on time

Cache entries persist beyond their TTL
Memory usage increases without new writes

## Objective

Restore timely eviction of expired cache entries

## Success Criteria

- The declared business operation returns HTTP 200.
- The expired-key lag reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
