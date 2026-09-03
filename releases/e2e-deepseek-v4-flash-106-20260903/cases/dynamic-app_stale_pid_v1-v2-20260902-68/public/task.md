# Operations task

The service responds to liveness checks but the declared operation does not meet its SLO; compare process lifecycle state and service health.

## Impact

A restart alone must not be treated as a durable repair for the failing operation.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Do not change the caller contract, disable validation, or replace the service.
- Use repeated live observations before declaring recovery.
- Use live observations before making a change. If a change requires multiple stages, follow the declared stage order and verify each transition.

## Public verification signals

- Restore the documented business operation using live state.
- Confirm that the underlying fault signal is gone, not merely hidden.
- Verify that the repair survives the applicable restart or reconciler boundary.
- Confirm the service has a live process identity that belongs to the intended application, not only a file with a numeric value.
- Confirm the service remains healthy after a lifecycle restart.
