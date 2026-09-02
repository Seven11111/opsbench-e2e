# Operations task

The service is experiencing a gradual increase in the number of open file handles it maintains. Over time, this can prevent the service from opening new files or network connections, leading to degraded performance and eventual unresponsiveness.

## Impact

Business operations that depend on the service (e.g., processing requests, accessing files) may fail or become slow. The service may become completely unavailable.

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
- Confirm file-descriptor usage remains stable with sufficient resource headroom.
