# Operations task

Prometheus is experiencing performance degradation: target refresh operations are failing, as indicated by an increasing `prometheus_sd_http_failures_total` counter. Additionally, some metrics are missing from scraped targets, and the overall system is slow.

## Impact

Monitoring gaps and delayed alerting due to incomplete or failed target refreshes.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Repair the underlying service state; do not disable monitoring or change the business contract.

## Public verification signals

- Prometheus reports the target as up.
- Prometheus readiness is healthy.
- The recovered target state remains valid after a restart.
