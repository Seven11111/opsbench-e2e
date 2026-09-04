# TLS handshake failures

Increased TLS handshake error rate in production traffic.
Certificate validation errors reported in logs with depth mismatch.

## Objective

Restore successful TLS handshake and certificate chain validation.

## Success Criteria

- The declared business operation returns HTTP 200.
- The chain order valid reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
