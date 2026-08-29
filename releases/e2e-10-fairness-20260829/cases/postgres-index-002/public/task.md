# Operations task

A database query that should return a moderate number of rows is running slowly; the query plan shows a sequential scan instead of an index scan, and the query takes several seconds to complete.

## Impact

Application response times are degraded, and the database server CPU usage is higher than expected for this workload.

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
