# Operations task

Fluent Bit HTTP input plugins pause their shared HTTP listener, causing incoming connections to be accepted and immediately closed. Clients see a connection close before a response arrives, and any in-flight requests are dropped. Data from HTTP sources is lost.

## Impact

Data ingestion from HTTP-based sources (e.g., http, splunk, elasticsearch, opentelemetry, prometheus_remote_write) stops; no new data is received and buffered.

## Objective

Diagnose the live incident, restore the service to its documented healthy state, and verify recovery.

## Constraints

- Use only the public task and runtime tools.
- Do not replace the service with a new implementation.
- Make the smallest safe repair and verify it from live state.
- Repair the underlying service state; do not disable monitoring or change the business contract.

## Public verification signals

- Fluent Bit health and metrics endpoints are available.
- The configured output is accepting records.
- The recovered delivery state remains valid after a restart.
