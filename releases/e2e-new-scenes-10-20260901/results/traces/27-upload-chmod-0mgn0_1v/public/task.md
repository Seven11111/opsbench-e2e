# Operations task

Upload requests to the document portal return HTTP 403 with 'Permission denied'. The application logs show that the upload directory `/var/www/uploads` is a symbolic link pointing to `/data/uploads`. The target directory has correct read/write permissions, but uploads still fail.

## Impact

Users cannot upload documents, halting business operations.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Use the live runtime tools to identify and repair the underlying operational state.

## Public verification signals

- The live health endpoint returns HTTP 200.
- The business operation remains usable after the repair.
- The repair preserves the service contract and remains valid after observation.
