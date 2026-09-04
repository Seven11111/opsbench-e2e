# HTTP 503 and low statistics freshness

Business operation returns HTTP 503.
Statistics freshness metric is below the healthy baseline.

## Objective

Restore statistics freshness and recover HTTP 200.

## Success Criteria

- The declared business operation returns HTTP 200.
- The statistics freshness reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
