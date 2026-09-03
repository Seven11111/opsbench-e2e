# Operations task

A service cannot reach its dependency (e.g., a database) over the internal network. Containers are running and healthy. The dependency is accessible from outside the network via the host port, but internal service-to-service communication fails.

## Impact

The service is unable to perform operations that depend on the dependency, leading to degraded functionality or errors.

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
