# Operations task

The orders API intermittently returns HTTP 503, while the application and
PostgreSQL health endpoints remain green. Failures become more frequent during
the periodic inventory synchronization window, but unrelated read-only reports
continue to complete.

## Impact

Customer order reads are delayed and occasionally fail. Restore stable order
reads without weakening the query contract, increasing the request timeout,
restarting PostgreSQL, or disrupting unrelated database work.

## Objective

Use live operational evidence to identify the causal runtime state, repair its
durable source, and verify that the incident does not recur after the relevant
worker lifecycle and workload replay.

## Constraints

- Use only the public task and runtime tools.
- Preserve existing order data and the public API contract.
- Do not terminate all database sessions or restart PostgreSQL.
- Do not increase statement, lock, or caller timeouts.
- Do not disable the inventory synchronization worker permanently.
- Apply the smallest safe repair supported by live evidence.

## Public success criteria

- Order reads remain successful across repeated probes.
- Periodic inventory synchronization still runs.
- Unrelated reporting activity is not interrupted.
- Recovery survives the relevant service lifecycle and workload replay.

