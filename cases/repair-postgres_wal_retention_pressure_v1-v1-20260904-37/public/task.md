# WAL headroom is shrinking

The orders operation returns HTTP 200, but retained WAL is above its normal range.

## Objective

Restore the live service and verify the technology signal.

## Success Criteria

- The business operation returns HTTP 200.
- PostgreSQL reports no abnormal retained WAL for the active slot.
- The repaired database state remains correct after restart.

Use only the provided bounded runtime tools. Do not replace the service or bypass validation.
