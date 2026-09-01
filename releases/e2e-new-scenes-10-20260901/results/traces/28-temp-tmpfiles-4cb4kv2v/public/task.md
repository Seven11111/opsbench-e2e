# Operations task

The systemd-tmpfiles service does not create the required temporary directory /tmp/service_dir at startup. The directory is missing, causing dependent services to fail with 'No such file or directory' errors. The systemd-tmpfiles service reports no error for the configuration line, indicating a silent failure.

## Impact

The service cannot store runtime files, breaking its normal operation. The documented workflow cannot complete.

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
