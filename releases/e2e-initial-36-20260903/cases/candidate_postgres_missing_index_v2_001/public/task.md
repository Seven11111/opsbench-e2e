# Operations task

A customer lookup that previously met its latency objective has become significantly slower and now uses a sequential scan. PostgreSQL remains healthy. Diagnose the live execution state, restore efficient query execution without changing the query's business semantics, and verify repeated latency.

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
