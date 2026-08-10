# Persistent CPU runaway recovery

The target service remains reachable, but a supervised background worker is
causing sustained CPU pressure. Diagnose the live process and configuration
state, apply a persistent repair, and verify the service after the supervisor
checks its configuration again.

## Impact

CPU pressure causes latency and throughput degradation even though the health
endpoint still responds.

## Objective

Stop the runaway workload through a persistent configuration repair. A one-time
process termination is not sufficient.

## Constraints

- Use only the public task and runtime tools.
- Make the smallest safe repair in the target container.
- Do not read evaluator files, scenario files, hidden labels, or host paths.

## Public verification signals

- The worker health endpoint returns HTTP 200.
- Repeated container CPU samples remain below the recovery threshold.
- The repair persists after the supervisor rechecks its configuration.
