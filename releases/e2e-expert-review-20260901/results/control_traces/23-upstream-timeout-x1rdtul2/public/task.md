# Operations task

Requests to the order endpoint are timing out while the upstream remains reachable. Recent probes show response latency above the 600 ms service objective and the gateway returns HTTP 504 for affected requests.

## Impact

Users cannot reliably complete the order operation within the declared response-time objective.

## Objective

Restore the order endpoint so successful responses complete under 600 ms while preserving the business contract. Do not merely increase the caller timeout.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Use the live runtime tools to identify and repair the underlying operational state.

## Public verification signals

- The live health endpoint returns HTTP 200.
- The order endpoint returns HTTP 200 and completes under 600 ms on repeated probes.
- The repair preserves the service contract and remains valid after observation and restart.
