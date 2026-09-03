# Operations task

The caller health endpoint is reachable, but a business operation fails after retries. The local process is healthy and the failure is associated with the effective downstream route.

## Impact

Requests cannot complete. Repair the effective dependency path without changing the caller contract, disabling validation, or hiding the symptom with a larger timeout; verify recovery after restart.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Do not bypass the service contract or disable validation.
- Use the public business check and available diagnostic evidence to form a root-cause hypothesis. Choose only a registered repair action supported by live signals; follow any protocol returned by the repair tool, and verify the business operation after recovery.

## Public verification signals

- The business request succeeds.
- The effective dependency route matches the healthy baseline and remains correct after restart.
- Repeated requests do not remain blocked by a stale protection state after recovery.
