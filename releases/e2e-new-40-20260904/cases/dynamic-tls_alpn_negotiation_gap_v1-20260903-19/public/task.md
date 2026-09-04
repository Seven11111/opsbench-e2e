# Decreased ALPN overlap rate

ALPN overlap metric dropped below 90% in the last hour.
HTTP/2 connections are failing to negotiate protocol.

## Objective

Restore ALPN overlap to healthy baseline.

## Success Criteria

- The declared business operation returns HTTP 200.
- The alpn overlap reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
