# Operations task

The worker container consumes excessive CPU.

## Impact

Host load is elevated and requests are delayed.

## Objective

Restore the service to a healthy state. Use the provided runtime tools, make the smallest safe change, and verify the result.

## Verification signals

- The worker health signal is healthy and resource usage returns to baseline.
