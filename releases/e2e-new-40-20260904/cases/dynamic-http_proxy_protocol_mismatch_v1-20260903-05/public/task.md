# Incorrect client IP addresses in application logs

Client IP addresses in application logs are showing incorrect origin IPs, causing authentication failures for trusted sources.

## Objective

Restore accurate client IP propagation from trusted proxies.

## Success Criteria

- The declared business operation returns HTTP 200.
- The proxy protocol match reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
