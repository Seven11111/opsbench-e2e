# TLS handshake fails with hostname verification error

Client application reports 'Hostname mismatch' error during TLS handshake.
SNI route match query returns empty result.

## Objective

Re-establish correct TLS certificate selection based on client SNI.

## Success Criteria

- The declared business operation returns HTTP 200.
- The sni route match reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
