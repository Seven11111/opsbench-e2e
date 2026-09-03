# Operations task

A declared business operation is unhealthy while the target process remains reachable; inspect request route and upstream response.

## Impact

The production-facing operation is unavailable or degraded and requires evidence-guided repair.

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
- Confirm the documented dependency remains reachable and its service contract is preserved.
- Confirm the effective dependency state remains correct after the lifecycle boundary.
