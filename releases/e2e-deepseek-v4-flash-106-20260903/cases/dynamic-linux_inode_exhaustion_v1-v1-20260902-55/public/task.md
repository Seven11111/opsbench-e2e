# Operations task

A declared business operation is unhealthy while the target process remains reachable; inspect service health and business response.

## Impact

The production-facing operation is unavailable or degraded and requires evidence-guided repair.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Use the live runtime tools to identify and repair the underlying operational state.

## Public verification signals

- The live health endpoint returns HTTP 200.
- The business operation remains usable after the repair.
- The repair preserves the service contract and remains valid after observation.
