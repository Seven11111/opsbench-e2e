# Persistent high scheduler runqueue

Runqueue length exceeds 10 per CPU core for over 5 minutes.
System load average remains above 80% of number of CPU cores.

## Objective

Restore runqueue load to healthy baseline.

## Success Criteria

- The declared business operation returns HTTP 200.
- The runqueue load reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
