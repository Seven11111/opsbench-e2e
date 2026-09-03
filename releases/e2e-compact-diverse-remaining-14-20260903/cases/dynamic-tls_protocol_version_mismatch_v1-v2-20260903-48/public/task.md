# TLS handshake fails with empty CertificateRequest CA list

Server sends an empty CA list in CertificateRequest during handshake
Client fails with 'certificate_required' alert and no mutual authentication

## Objective

Restore successful TLS handshake with proper CA list and name check compliance

## Success Criteria

- The declared business operation returns HTTP 200.
- The protocol overlap reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
