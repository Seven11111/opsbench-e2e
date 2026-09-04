# Remote write pending queue growing

Remote write pending queue length is increasing and not decreasing.
WAL read progress is stalled.

## Objective

Restore normal remote write throughput and clear pending queue.

## Success Criteria

- The declared business operation returns HTTP 200.
- The remote write pending reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
