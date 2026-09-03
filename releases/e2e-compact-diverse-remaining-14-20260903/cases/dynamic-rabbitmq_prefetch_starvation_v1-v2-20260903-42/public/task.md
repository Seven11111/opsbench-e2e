# Consumer acknowledgements stalled

Queue depth is increasing while consumers are idle.
Unacknowledged message count is stuck at the per-consumer prefetch limit.

## Objective

Restore consumer acknowledgement flow and reduce unacknowledged message count to baseline.

## Success Criteria

- The declared business operation returns HTTP 200.
- The unacked messages reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
