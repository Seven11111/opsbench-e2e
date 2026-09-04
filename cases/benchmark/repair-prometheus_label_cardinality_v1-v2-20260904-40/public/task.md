# Metrics queries are slowing

The target is scrapeable, but Prometheus reports excessive active series.

## Objective

Restore the live service and verify the technology signal.

## Success Criteria

- The business operation returns HTTP 200.
- Prometheus reports the target series count within the healthy range.
- The scrape remains healthy after restart.

Use only the provided bounded runtime tools. Do not replace the service or bypass validation.
