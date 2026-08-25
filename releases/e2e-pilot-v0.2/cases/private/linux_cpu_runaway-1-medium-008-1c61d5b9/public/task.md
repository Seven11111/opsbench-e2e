# Operations task

A worker container still consumes excessive CPU even though the documented runaway worker setting appears to be disabled; host load remains elevated and requests are delayed.

## Impact

Service remains degraded because the high CPU condition persists, continuing to delay requests and consume host capacity.

## Objective

Restore the service to a healthy state. Use the provided runtime tools, make the smallest safe change, and verify the result.

## Verification signals

- The worker health signal is healthy and resource usage returns to baseline.
