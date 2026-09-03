# High cache eviction rate and low hit ratio

Cache eviction counters are elevated above baseline, and cache hit ratio has dropped below 90%.

## Objective

Restore cache hit ratio and reduce eviction rate to healthy baseline

## Success Criteria

- business operation returns HTTP 200
- evicted keys returns to a healthy baseline
- repaired behavior survives restart
