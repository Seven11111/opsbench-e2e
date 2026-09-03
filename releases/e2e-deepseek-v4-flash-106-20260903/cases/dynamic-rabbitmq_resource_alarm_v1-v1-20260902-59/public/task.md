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

- RabbitMQ reports no resource alarm.
- A queue operation remains available.
- The recovered broker state remains valid after a restart.
