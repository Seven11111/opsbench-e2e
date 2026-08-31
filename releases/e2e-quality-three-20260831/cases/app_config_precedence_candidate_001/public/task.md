# Operations task

The HTTP service is not reachable on the expected endpoint. It is using a configuration value that originates from a higher-precedence layer instead of the intended source, causing the service to behave incorrectly.

## Impact

Clients cannot communicate with the service, disrupting normal operations.

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
- Confirm the effective service behavior is healthy, not merely that one visible setting changed.
