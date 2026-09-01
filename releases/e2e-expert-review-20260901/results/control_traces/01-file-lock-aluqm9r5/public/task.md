# Operations task

The file-processing worker is repeatedly failing when it tries to obtain the report lock. The health endpoint and the file-processing operation are affected, and the problem may return after a short observation period even if the worker appears to recover briefly.

## Impact

New reports remain unprocessed and the backlog grows. Preserve the existing file-processing and locking contract while restoring the operation.

## Objective

Diagnose the live lock condition, restore reliable report processing, and verify that the repair remains effective after the declared observation boundary.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Do not treat killing one process or deleting one lock file as sufficient unless the live lock condition remains absent.

## Public verification signals

- The live health endpoint returns HTTP 200.
- The business operation remains usable after the repair.
- A repeated report-processing attempt can obtain and release the report lock.
- The repair preserves the service contract and remains valid after observation.
