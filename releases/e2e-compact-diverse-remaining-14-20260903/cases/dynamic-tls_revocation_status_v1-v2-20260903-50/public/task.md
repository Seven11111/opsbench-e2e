# Certificate chain depth verification failure during TLS handshake

TLS handshake fails with certificate verification error.
OpenSSL reports depth value exceeding expected chain length.

## Objective

Restore successful TLS handshake with valid certificate chain.

## Success Criteria

- The declared business operation returns HTTP 200.
- The revocation status reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
