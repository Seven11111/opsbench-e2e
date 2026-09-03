# High eviction count and low cache hit ratio

Eviction counters elevated above threshold
Cache hit ratio dropped below 80%

## Objective

Restore cache hit ratio and eviction count to normal levels

## Success Criteria

- business operation returns HTTP 200
- evicted keys returns to a healthy baseline
- repaired behavior survives restart
