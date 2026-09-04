# Swap headroom critically low

Swap free space is less than 10% of total swap.
System response time degrades.

## Objective

Restore swap headroom to a healthy level

## Success Criteria

- The declared business operation returns HTTP 200.
- The swap headroom reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
