# Operations task

Event processing is reachable, but the consumer group's progress is not advancing.

## Impact

The declared business operation is degraded and requires evidence-guided recovery.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Do not replace the service or bypass the native technology checks.
- Use live evidence before applying a bounded repair.

## Public verification signals

- The event operation returns HTTP 200.
- The consumer group offset is progressing with bounded lag.
- The result remains healthy after restart.
