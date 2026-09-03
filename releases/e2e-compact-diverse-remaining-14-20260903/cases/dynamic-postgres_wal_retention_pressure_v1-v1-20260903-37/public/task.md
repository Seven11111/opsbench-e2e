# High WAL retention

WAL directory size exceeds 10 GB
Replica lag exceeds 30 seconds

## Objective

Reduce WAL retention to healthy baseline

## Success Criteria

- business operation returns HTTP 200
- wal retained bytes returns to a healthy baseline
- repaired behavior survives restart
