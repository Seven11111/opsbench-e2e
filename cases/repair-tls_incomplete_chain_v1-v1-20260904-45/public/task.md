# Some HTTPS clients cannot connect

The TLS port accepts connections, but a normal trust check fails.

## Objective

Restore the live service and verify the technology signal.

## Success Criteria

- The HTTPS business operation returns HTTP 200.
- A trust-checked TLS handshake succeeds.
- The verified HTTPS operation remains healthy after restart.

Use only the provided bounded runtime tools. Do not replace the service or bypass validation.
