# Legacy HTTPS clients fail

The TLS port accepts connections, but a TLS 1.2 client cannot negotiate.

## Objective

Restore the live service and verify the technology signal.

## Success Criteria

- The HTTPS business operation returns HTTP 200.
- The documented TLS 1.2 handshake succeeds.
- The verified HTTPS operation remains healthy after restart.

Use only the provided bounded runtime tools. Do not replace the service or bypass validation.
