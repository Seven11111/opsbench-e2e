# Operations task

If disabled, redirects issued by nginx will be relative.

## Impact

The documented operational workflow cannot complete reliably.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.

## Public verification signals

- The Nginx health endpoint returns HTTP 200 on the documented service port.
- The repaired service remains healthy after a short observation window.
