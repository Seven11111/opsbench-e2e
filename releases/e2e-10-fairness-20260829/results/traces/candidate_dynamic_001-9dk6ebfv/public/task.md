# Operations task

A database query on a large table is using a sequential scan instead of an index scan, causing high query latency and poor performance. The query plan shows a Seq Scan node.

## Impact

Slow query response times, potential timeouts, and degraded application performance.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Use the PostgreSQL client through the provided runtime.

## Public verification signals

- The customer lookup returns the expected rows.
- EXPLAIN shows an index-backed plan for the lookup.
- Repeated execution remains below the case latency threshold.
