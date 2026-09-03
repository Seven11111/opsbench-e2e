# Operations task

The service responds to liveness checks but the declared operation does not meet its SLO; compare service health and business response.

## Impact

A restart alone must not be treated as a durable repair for the failing operation.

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
