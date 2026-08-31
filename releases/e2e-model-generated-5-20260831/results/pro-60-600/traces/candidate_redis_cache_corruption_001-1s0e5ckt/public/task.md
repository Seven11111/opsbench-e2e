# Operations task

The catalog endpoint rejects its live payload while Redis responds normally to health checks. The service is reachable, but the application-level cache contract is not satisfied.

## Impact

Catalog reads are unavailable. Restore a valid payload without deleting the key, disabling validation, or changing the consumer contract, and verify the result after a lifecycle boundary.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Do not bypass the service contract or disable validation.
- Use the public business check and available diagnostic evidence to form a root-cause hypothesis. Choose only a registered repair action supported by live signals; follow any protocol returned by the repair tool, and verify the business operation after recovery.
- For the cache case, the prepare stage must happen before the payload is rebuilt; do not delete the cache key.

## Public verification signals

- The catalog payload is valid.
- The cache contract remains intact.
