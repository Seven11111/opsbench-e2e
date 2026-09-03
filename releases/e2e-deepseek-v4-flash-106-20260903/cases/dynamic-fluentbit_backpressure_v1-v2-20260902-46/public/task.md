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
- Repair the underlying service state; do not disable monitoring or change the business contract.

## Public verification signals

- Fluent Bit health and metrics endpoints are available.
- The configured output is accepting records.
- The recovered delivery state remains valid after a restart.
