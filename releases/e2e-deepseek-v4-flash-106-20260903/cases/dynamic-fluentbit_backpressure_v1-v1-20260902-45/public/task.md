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
- Repair the underlying service state; do not disable monitoring or change the business contract.

## Public verification signals

- Fluent Bit health and metrics endpoints are available.
- The configured output is accepting records.
- The recovered delivery state remains valid after a restart.
