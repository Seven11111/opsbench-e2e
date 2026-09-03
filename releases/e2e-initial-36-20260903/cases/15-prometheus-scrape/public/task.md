# Operations task

The Prometheus server is ready, but the configured application target is not being scraped successfully. The target's metrics are missing from Prometheus and the monitoring gap is affecting alerting.

## Impact

Monitoring gaps and delayed alerting because one declared target is not producing its expected metrics.

## Objective

Restore the declared scrape target and verify that live target metrics are collected again. Do not disable scraping or replace the exporter.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Repair the underlying service state; do not disable monitoring or change the business contract.

## Public verification signals

- Prometheus reports the target as up.
- Prometheus readiness is healthy.
- The target's `opsbench_target_up` metric is collected.
- The recovered target state remains valid after a restart.
