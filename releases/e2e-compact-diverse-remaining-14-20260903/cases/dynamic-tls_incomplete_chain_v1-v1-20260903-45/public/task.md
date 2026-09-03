# TLS handshake failures

TLS handshake attempts fail with certificate verification error.
Client connections are rejected.

## Objective

Restore successful TLS handshake and certificate chain verification.

## Success Criteria

- The declared business operation returns HTTP 200.
- The chain depth reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
