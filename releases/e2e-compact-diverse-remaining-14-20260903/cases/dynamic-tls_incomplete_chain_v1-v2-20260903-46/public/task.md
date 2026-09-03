# keyUsage mismatch certificate errors

Handshake fails with 'keyUsage mismatch' error for previously valid certificates
Certificate chain depth drops as intermediate certificates are rejected

## Objective

Restore handshake success by correcting keyUsage verification configuration

## Success Criteria

- The declared business operation returns HTTP 200.
- The chain depth reading returns to its healthy baseline.
- The repaired behavior remains after a service restart.
