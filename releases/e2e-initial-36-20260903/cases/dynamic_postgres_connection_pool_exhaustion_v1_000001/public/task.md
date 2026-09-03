# Operations task

The query endpoint returns HTTP 503 although PostgreSQL is reachable and the target process is healthy. The failure is correlated with a gradual loss of available database capacity.

## Impact

Application requests cannot obtain a connection. Preserve the query and service contract; a one-time restart or a larger caller timeout is not a durable repair.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Do not bypass the service contract or disable validation.
- Use the public business check and available diagnostic evidence to form a root-cause hypothesis. Choose only a registered repair action supported by live signals; follow any protocol returned by the repair tool, and verify the business operation after recovery.

## Public verification signals

- Queries return HTTP 200.
- Pool-holder sessions are gone.
- Recovery persists.
