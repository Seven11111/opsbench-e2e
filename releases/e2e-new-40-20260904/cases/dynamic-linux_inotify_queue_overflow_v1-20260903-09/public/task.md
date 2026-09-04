# Critically low inotify queue headroom

inotify queue headroom is below 10% of maximum capacity.
New inotify watch creation requests are failing.

## Objective

Restore inotify queue headroom to a healthy baseline.

## Success Criteria

- The declared business operation returns HTTP 200.
- The inotify queue headroom reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
