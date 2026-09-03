# Scrape failures and high active series count

Prometheus scrape errors increasing, active series count exceeding 90% of configured limit

## Objective

Reduce active series count to safe level and restore scrape health

## Success Criteria

- The declared business operation returns HTTP 200.
- The series headroom reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
