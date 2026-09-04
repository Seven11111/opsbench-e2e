# Application access errors on mounted volumes

Application returns 'Permission denied' when accessing mounted directories
Container process runs as root instead of expected non-root user

## Objective

Ensure application runs with its designated user ID

## Success Criteria

- The declared business operation returns HTTP 200.
- The effective uid reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
