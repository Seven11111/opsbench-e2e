# Ack timeout count spike

Ack timeout count is above threshold.
Consumer logs show repeated delivery failures.

## Objective

Restore normal ack timeout count and ensure business operation responds successfully.

## Success Criteria

- The declared business operation returns HTTP 200.
- The ack timeout count reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
