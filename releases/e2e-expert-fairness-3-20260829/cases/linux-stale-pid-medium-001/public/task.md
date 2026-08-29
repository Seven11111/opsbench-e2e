# Operations task

The HTTP service is reported as active by the system service manager, but health checks against the service fail. The service does not respond to requests, and the service manager indicates the service started successfully even though the service binary is not functioning.

## Impact

Users cannot access the HTTP service, causing downtime.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Use the live runtime tools to identify and repair the underlying operational state.

## Public verification signals

- The live health endpoint returns HTTP 200.
- The business operation remains usable after the repair.
- The repair preserves the service contract and remains valid after observation.
