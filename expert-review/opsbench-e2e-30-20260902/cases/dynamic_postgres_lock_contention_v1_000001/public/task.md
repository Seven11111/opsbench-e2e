# Operations task

The orders endpoint intermittently returns HTTP 503 while both the application and PostgreSQL health checks remain green. The failure appears only while a live database session is present.

## Impact

Customer order reads are delayed, but replacing the query, changing the client timeout, or restarting only the application must not be treated as the repair.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Do not bypass the service contract or disable validation.
- Use the public business check and available diagnostic evidence to form a root-cause hypothesis. Choose only a registered repair action supported by live signals; follow any protocol returned by the repair tool, and verify the business operation after recovery.

## Public verification signals

- Orders return HTTP 200.
- The blocking session is absent.
- Recovery remains after restart.
