# Operations task

The worker health signal has become unreliable while the service is still reachable. Repeated live observations show the worker's memory usage growing and approaching its declared resource budget; the same workload should remain available while the resource signal is stabilized.

## Impact

The worker may exhaust its memory headroom and the documented workflow cannot complete reliably. Preserve the service's HTTP and workload contract while resolving the resource pressure.

## Objective

Diagnose the live memory signal, stop the abnormal growth at its source, and verify both business recovery and stable memory headroom after the observation boundary.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Do not claim recovery from a single health response; inspect repeated resource observations.

## Public verification signals

- The live health endpoint returns HTTP 200.
- The live metrics endpoint reports memory usage below the declared memory limit.
- Repeated observations show that memory growth is no longer active.
- The business operation remains usable and the repair persists after observation.
