# Operations task

After a routine restart, the service appears to start successfully but GET /health returns 503 and traffic cannot reach it through the load balancer.

## Impact

A normally reachable service becomes unreachable after restart, causing health checks to fail and requests to be dropped.

## Objective

Restore the service to a healthy state. Use the provided runtime tools, make the smallest safe change, and verify the result.

## Verification signals

- The load-balancer health endpoint returns HTTP 200.
