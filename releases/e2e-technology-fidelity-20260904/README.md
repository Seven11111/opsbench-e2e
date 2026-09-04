# Technology-fidelity replacement cases

This release contains ten new replacement E2E cases generated on 2026-09-04
with the `e2e-technology-fidelity-v2` contract.

## Scope

The cases cover Linux file-descriptor pressure, Linux process-limit
exhaustion, systemd restart throttling, PostgreSQL deadlocks, PostgreSQL
replication-slot retention, Kafka offset commit failure, RabbitMQ consumer
ack timeout, Prometheus scrape timeout mismatch, TLS certificate-chain order,
and TLS SNI route mismatch.

The old 40-case pool is frozen and is not modified or used as provenance for
this release. Each case has fresh official-document provenance and records its
replacement lineage only through `replaces_case_id`.

## Validation status

- 10/10 cases generated successfully.
- 10/10 cases passed `static_review_case`.
- The strict review covers causal technology identity, Compose, injection,
  diagnosis, recovery, task/tool/verifier alignment, diagnosability, and
  shortcut resistance.
- `benchmark_eligible` remains `false`.
- Docker runtime gate and Agent calibration have not been run for this release.

See `reports/static_review.json` for the frozen static-review report and
`provenance/` plus `evidence/bundles/` for the fresh source records.
