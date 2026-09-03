# Operations task

RabbitMQ node raises a memory alarm and blocks all connections that are publishing messages.

## Impact

Publishers cannot send messages; once the alarm clears, normal service resumes.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Repair the underlying service state; do not disable monitoring or change the business contract.

## Public verification signals

- RabbitMQ reports no resource alarm.
- A queue operation remains available.
- The recovered broker state remains valid after a restart.
