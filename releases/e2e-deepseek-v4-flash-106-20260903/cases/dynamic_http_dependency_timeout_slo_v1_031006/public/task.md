# Operations task

Clients experience slow response times and intermittent timeouts when requesting large payloads through the proxy. The proxy logs show read timeouts.

## Impact

Business operations that depend on large response payloads (e.g., file downloads, API responses with large bodies) fail intermittently.

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
- Confirm dependency responses meet the documented latency objective.
- Confirm the downstream delay is no longer causing the business request to exceed its objective.
