# PostgreSQL lookup-plan recovery

A common customer lookup still returns data, but its query plan has degraded
and the lookup is slower than the service baseline. Use the PostgreSQL client
and `EXPLAIN` to diagnose the live plan, make the smallest safe schema repair,
and verify both correctness and performance.

## Impact

The lookup consumes more database work than necessary and causes increased
latency for requests that depend on it.

## Objective

Restore an index-backed plan for the target lookup while preserving its result
set. Re-run the query after the repair to verify the improvement.

## Constraints

- Use only the public task and runtime tools.
- Use the PostgreSQL client through the provided runtime.
- Make the smallest safe schema repair; do not replace the database.
- Do not read evaluator files, scenario files, hidden labels, or host paths.

## Public verification signals

- The customer lookup returns the expected rows.
- `EXPLAIN` shows an index-backed plan for the lookup.
- Repeated execution remains below the case latency threshold.
