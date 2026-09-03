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

## Public verification signals

- The Nginx health endpoint returns HTTP 200 on the documented service port.
- The repaired service remains healthy after a short observation window.
