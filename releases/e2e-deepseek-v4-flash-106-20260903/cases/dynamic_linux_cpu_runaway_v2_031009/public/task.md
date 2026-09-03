# Operations task

The CPU pressure stall indicator (PSI) shows that the 'some' avg10 value is consistently above 20% (threshold), indicating that tasks are frequently stalled on CPU. The service response time has increased by 3x.

## Impact

Users experience slow response times and potential timeouts.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.

## Public verification signals

- The worker health endpoint returns HTTP 200.
- Container CPU usage remains below the recovery threshold for repeated samples.
- The repair persists after the worker supervisor checks its configuration again.
