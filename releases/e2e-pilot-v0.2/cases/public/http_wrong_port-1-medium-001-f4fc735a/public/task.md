# Operations task

The HTTP health endpoint returns 503.

## Impact

Requests cannot reach the service through the load balancer.

## Objective

Restore the service to a healthy state. Use the provided runtime tools, make the smallest safe change, and verify the result.

## Verification signals

- The load-balancer health endpoint returns HTTP 200.
