# Operations task

CPU pressure stall indicators (some avg10, avg60, avg300) in /proc/pressure/cpu show elevated values, indicating that tasks are frequently stalled on CPU resources. The worker process consumes excessive CPU cycles, causing service degradation.

## Impact

System responsiveness drops, service response times increase, and the workload may experience throughput loss.

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
