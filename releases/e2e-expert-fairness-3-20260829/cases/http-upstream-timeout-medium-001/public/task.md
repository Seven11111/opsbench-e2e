# Operations task

Requests to an upstream backend service return HTTP 502 Bad Gateway errors or timeouts. The first part of the response often exceeds the configured buffer size, causing the response to be considered invalid.

## Impact

Users are unable to access features that depend on this backend service, causing service degradation.

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
