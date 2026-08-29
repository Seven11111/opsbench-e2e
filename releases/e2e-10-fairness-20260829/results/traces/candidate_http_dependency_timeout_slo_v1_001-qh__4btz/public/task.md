# Operations task

The application experiences intermittent timeouts when making requests to a backend service. Timeouts occur even when the backend is responsive, and the problem is more noticeable with responses that are larger or slow to transmit. The connection is closed if the proxied server does not transmit anything within the timeout period.

## Impact

Clients receive incomplete responses or connection errors, leading to failed operations and degraded user experience. The proxy does not attempt to read the whole response from the upstream server, so partial transmissions can abort.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Do not change the caller contract, disable validation, or replace the service.
- Use repeated live observations before declaring recovery.
- Use live observations before making a change. If a change requires multiple stages, follow the declared stage order and verify each transition.
- Keep the documented request latency objective below 600 milliseconds.

## Public verification signals

- Restore the documented business operation using live state.
- Confirm that the underlying fault signal is gone, not merely hidden.
- Verify that the repair survives the applicable restart or reconciler boundary.
