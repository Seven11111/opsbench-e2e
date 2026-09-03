# Operations task

The Kafka broker is healthy, but the consumer-group lag endpoint reports that processing is not making progress. The target service remains running while the backlog grows.

## Impact

Downstream event processing is delayed. Diagnose group/consumer state, preserve the topic and message contract, and prove that recovery remains stable across repeated observations.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Do not bypass the service contract or disable validation.
- Use the public business check and available diagnostic evidence to form a root-cause hypothesis. Choose only a registered repair action supported by live signals; follow any protocol returned by the repair tool, and verify the business operation after recovery.
- For the lag case, quiesce the backlog producer during prepare before resuming the consumer during apply.

## Public verification signals

- Consumer lag is below five messages.
- The consumer resumes processing.
