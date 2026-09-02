# Operations task

A database query that is expected to use an index is instead performing a sequential scan, causing significantly slower execution times. The query plan, examined via EXPLAIN, shows a sequential scan even though an appropriate index exists.

## Impact

Application response times degrade, and overall database performance is reduced, potentially affecting user experience and system throughput.

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
