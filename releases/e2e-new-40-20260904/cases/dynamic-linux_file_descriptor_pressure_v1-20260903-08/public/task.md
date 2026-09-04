# File descriptor headroom depletion

Number of open file descriptors exceeds 80% of the system limit
Application logs contain 'too many open files' error messages

## Objective

Recover sufficient file descriptor headroom

## Success Criteria

- The declared business operation returns HTTP 200.
- The file descriptor headroom reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
