# Operations task

The service becomes healthy briefly and then repeatedly disappears as its process restart count keeps increasing.

## Impact

The production-facing operation is unavailable or degraded and requires evidence-guided repair.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Use the declared live health and metrics channels; do not bypass the service contract.

## Public verification signals

- The declared business operation returns HTTP 200.
- The live diagnostic signal is absent after repair.
- The repair remains effective after the service lifecycle is checked again.
