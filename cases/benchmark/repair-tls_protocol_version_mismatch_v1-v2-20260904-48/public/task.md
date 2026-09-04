# HTTPS negotiation is inconsistent

Modern clients connect, while the documented legacy handshake reports a protocol error.

## Objective

Restore the live service and verify the technology signal.

## Success Criteria

- The HTTPS business operation returns HTTP 200.
- The documented TLS 1.2 handshake succeeds.
- The verified HTTPS operation remains healthy after restart.

Use only the provided bounded runtime tools. Do not replace the service or bypass validation.
