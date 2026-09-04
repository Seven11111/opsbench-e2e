# Expired message rate is elevated

Expired message rate is consistently above 100 messages per second.
Queue depth remains high despite TTL expiration.

## Objective

Restore normal expired message processing and queue depth.

## Success Criteria

- The declared business operation returns HTTP 200.
- The expired message rate reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
