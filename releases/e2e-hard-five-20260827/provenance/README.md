# Provenance Layout

Each directory under `generation` corresponds to one selected case package.
Copied artifacts preserve the generation run structure:

- `input/`: input document records;
- `evidence/`: evidence bundles and source excerpts;
- `provenance/`: document and claim provenance;
- `candidates/`: candidate and ScenarioSpec artifacts;
- `reviews/`: model or deterministic review artifacts;
- `revisions/`: revision history;
- `rejects/`: rejected artifacts, if any;
- `reports/`: validation and runtime reports;
- `manifest.json`: run-level metadata.

The main source topics represented are PostgreSQL explicit locking and
monitoring, Redis expiration/data types/patterns, Confluent consumer lag and
Apache Kafka consumer configuration, and the circuit breaker pattern.

Full cleaned source excerpts are retained under each case's `evidence/source`
directory. Evidence links in candidate and scenario artifacts point to the
corresponding source records.

Absolute paths that may appear in copied historical logs are provenance from
the producing workstation. They are not required to reproduce the cases; case
packages use relative Compose paths.
