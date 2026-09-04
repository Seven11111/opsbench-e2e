# Service alias resolution returning outdated IP addresses

Service A cannot reach Service B by its docker-compose alias, receiving 'connection refused' errors.
DNS resolution within the compose network returns an IP address that no longer corresponds to a running container.

## Objective

Restore alias resolution to reflect current container IPs so that cross-service communication works reliably.

## Success Criteria

- The declared business operation returns HTTP 200.
- The service alias resolution reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
