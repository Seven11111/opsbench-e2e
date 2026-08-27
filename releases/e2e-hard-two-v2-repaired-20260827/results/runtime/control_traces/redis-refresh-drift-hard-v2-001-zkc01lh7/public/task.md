# Operations task

The catalog API intermittently returns HTTP 503 even though Redis connectivity,
key existence, and service health checks remain green. The cached value is
valid JSON, and a direct correction can appear successful before the incident
returns during a later refresh cycle.

## Impact

Catalog reads are unreliable. Restore a durable cache representation while
preserving the catalog contract, refresh behavior, and expiration policy.

## Objective

Use live cache, application, configuration, and process evidence to identify
why the invalid representation returns, repair the durable source of the
problem, and verify recovery across a refresh lifecycle.

## Constraints

- Use only the public task and runtime tools.
- Do not delete the active catalog key.
- Do not disable payload validation or change the consumer contract.
- Do not disable the refresh worker permanently.
- Preserve the configured expiration policy.
- Apply the smallest safe repair supported by live evidence.

## Public success criteria

- Catalog reads remain valid across repeated refresh cycles.
- The refresh worker continues to update the cache.
- The active key remains present with the expected expiration behavior.
- Unrelated preview-cache data is not modified.

