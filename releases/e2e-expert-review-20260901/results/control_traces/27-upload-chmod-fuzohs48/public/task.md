# Operations task

Upload requests to the document portal fail with HTTP 403 and `Permission denied` when the service writes to `/data/uploads`.

## Impact

Users cannot upload documents, halting the document workflow.

## Objective

Restore uploads while preserving the service account and shared-directory permission contract. The directory must remain writable for the service worker, but must not grant write access to unrelated users.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Use the live runtime tools to identify and repair the underlying operational state.

## Public verification signals

- The live health endpoint returns HTTP 200.
- A test upload succeeds.
- The upload directory remains group-writable and not world-writable after observation and restart.
