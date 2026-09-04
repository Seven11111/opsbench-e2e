# Cache hot key wait spike

Hot key wait metric is 3x above baseline.
Cache get latency increase observed.

## Objective

Restore hot key wait to healthy baseline.

## Success Criteria

- The declared business operation returns HTTP 200.
- The hot key wait reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
