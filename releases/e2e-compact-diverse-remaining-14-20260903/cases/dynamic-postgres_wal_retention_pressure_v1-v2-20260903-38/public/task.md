# WAL retention growing beyond threshold

WAL retained bytes continuously increasing over 24 hours.
Replica lag exceeds 5 minutes.

## Objective

Restore WAL retention to healthy baseline and ensure replica freshness.

## Success Criteria

- business operation returns HTTP 200
- wal retained bytes returns to a healthy baseline
- repaired behavior survives restart
