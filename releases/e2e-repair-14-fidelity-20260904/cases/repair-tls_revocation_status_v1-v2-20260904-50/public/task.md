# Certificate status is stale

The service is reachable, but a trust client rejects the current certificate status.

## Objective

Restore the live service and verify the technology signal.

## Success Criteria

- The HTTPS business operation returns HTTP 200.
- The certificate passes the declared revocation check.
- The verified HTTPS operation remains healthy after restart.

Use only the provided bounded runtime tools. Do not replace the service or bypass validation.
