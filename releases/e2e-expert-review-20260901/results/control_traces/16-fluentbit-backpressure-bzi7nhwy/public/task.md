# Operations task

The log agent accepts input, but records are not reaching the downstream sink. Its health endpoint remains available while delivery pressure persists and recently submitted records are not observed downstream.

## Impact

Operational records are delayed or lost at the output boundary, so downstream consumers do not receive the events they need.

## Objective

Restore record delivery while preserving the input/output contract. Verify that a new record is received downstream and that delivery remains healthy after reload or restart.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Repair the underlying service state; do not disable monitoring or change the business contract.

## Public verification signals

- Fluent Bit health and metrics endpoints are available.
- A test record accepted by the input is received by the configured downstream sink.
- The configured output is accepting records.
- The recovered delivery state remains valid after a restart.
