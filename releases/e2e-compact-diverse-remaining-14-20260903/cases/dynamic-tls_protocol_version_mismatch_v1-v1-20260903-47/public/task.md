# Client certificate request failure

TLS handshake fails with 'certificate_unknown' alert
Server does not include client's CA in its acceptable CA list

## Objective

Restore successful TLS handshake with client certificate authentication

## Success Criteria

- The declared business operation returns HTTP 200.
- The protocol overlap reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
