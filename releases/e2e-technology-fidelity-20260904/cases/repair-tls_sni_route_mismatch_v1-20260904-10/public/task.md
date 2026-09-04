# Operations task

The secure endpoint is reachable, but one documented hostname presents the wrong identity.

## Impact

The declared business operation is degraded and requires evidence-guided recovery.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Do not replace the service or bypass the native technology checks.
- Use live evidence before applying a bounded repair.

## Public verification signals

- The secure business operation returns HTTP 200.
- Each documented hostname presents its correct certificate identity.
- The result remains healthy after restart.
