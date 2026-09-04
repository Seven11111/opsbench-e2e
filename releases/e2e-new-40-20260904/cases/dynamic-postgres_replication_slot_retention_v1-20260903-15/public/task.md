# WAL accumulation on primary

WAL segment count on the primary is continuously increasing, and the replication slot's confirmed_flush_lsn is not advancing.

## Objective

Restore WAL retention to a healthy baseline and ensure replication resumes normally.

## Success Criteria

- The declared business operation returns HTTP 200.
- The slot wal retention reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
