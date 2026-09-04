# Scrape timeout errors observed

Scrape timeout errors are persistently occurring. Metrics are missing for several targets.

## Objective

Restore reliable metric collection without timeout errors.

## Success Criteria

- The declared business operation returns HTTP 200.
- The scrape timeout errors reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
