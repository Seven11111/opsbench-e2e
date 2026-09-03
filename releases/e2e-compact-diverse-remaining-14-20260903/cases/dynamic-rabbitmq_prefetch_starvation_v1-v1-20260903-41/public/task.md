# Unacknowledged messages accumulating on consumer queues

Consumer queues show increasing unacknowledged message count
New messages are not being delivered to consumers despite available capacity

## Objective

Restore consumer message delivery and drain unacknowledged messages

## Success Criteria

- The declared business operation returns HTTP 200.
- The unacked messages reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
