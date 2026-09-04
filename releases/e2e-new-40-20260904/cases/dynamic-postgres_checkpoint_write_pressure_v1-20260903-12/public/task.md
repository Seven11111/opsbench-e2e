# Checkpoint delays and growing standby replay lag

Checkpoint completion time is increasing.
Standby replay lag is growing.

## Objective

Reduce checkpoint delay and restore normal WAL replay.

## Success Criteria

- The declared business operation returns HTTP 200.
- The checkpoint timing reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
