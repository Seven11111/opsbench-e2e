# Operations task

A Python application that processes files using file locking raises an `OSError` exception when attempting to acquire an exclusive lock with the non-blocking flag. The error prevents the application from continuing its file processing routine. Evidence from the Python documentation confirms that when a `fcntl()` or `lockf()` call fails, an `OSError` is raised, and if `LOCK_NB` is used and the lock cannot be acquired, the exception includes an `errno` attribute set to `EACCES` or `EAGAIN.

## Impact

The application is unable to process new files, leading to a backlog of unprocessed work. Additionally, if the application attempts to write without a proper lock, data corruption or segmentation violations may occur, as described in the documentation: 'this is most likely to result in a segmentation violation or a more subtle data corruption.'

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
