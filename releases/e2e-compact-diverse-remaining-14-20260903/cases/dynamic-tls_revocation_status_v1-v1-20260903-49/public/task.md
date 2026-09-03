# TLS handshake failure with certificate error

TLS client connections fail with 'certificate verify failed' error.
OpenSSL logs show a depth error during certificate chain verification.

## Objective

Restore correct certificate chain verification to allow successful TLS handshakes.

## Success Criteria

- The declared business operation returns HTTP 200.
- The revocation status reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
