# Nginx listener recovery

The HTTP service in the target container is unavailable. Diagnose the live
Nginx instance using the provided tools, identify why its configured listener
cannot start, and restore the service without replacing Nginx.

## Impact

Requests to the service port fail and the health endpoint is unavailable.

## Objective

Restore the existing Nginx service and verify that it remains healthy after a
short observation window.

## Constraints

- Use only the public task and runtime tools.
- Make the smallest safe repair in the target container.
- Do not read evaluator files, scenario files, hidden labels, or host paths.

## Public verification signals

- The Nginx health endpoint returns HTTP 200 on the service port.
- An Nginx master process is running after the repair.
