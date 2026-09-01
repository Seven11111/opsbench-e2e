# Operations task

TLS connections to the service are failing with certificate validation errors. Clients attempting to establish secure connections receive errors indicating that the server certificate validation has failed.

## Impact

The service is unable to complete TLS handshakes with proper hostname verification. Secure communication with clients is disrupted.

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
- Confirm the documented secure endpoint is usable with normal certificate and hostname verification.
