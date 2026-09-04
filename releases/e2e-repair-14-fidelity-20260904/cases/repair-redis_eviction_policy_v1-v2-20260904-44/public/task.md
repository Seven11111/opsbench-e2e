# Cache memory behavior changed

The catalog operation returns HTTP 200, but Redis reports the wrong memory policy.

## Objective

Restore the live service and verify the technology signal.

## Success Criteria

- The catalog operation returns HTTP 200.
- Redis reports the healthy memory policy and stable eviction behavior.
- The catalog operation remains healthy after restart.

Use only the provided bounded runtime tools. Do not replace the service or bypass validation.
