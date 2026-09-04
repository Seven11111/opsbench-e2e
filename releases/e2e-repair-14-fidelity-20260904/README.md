# Technology-Fidelity Repair Snapshot: 14 E2E Cases

This release contains the 14 case packages repaired after expert review of the
compact diverse snapshot. The replacements use technology-faithful runtime
objects and public observation paths for PostgreSQL, Prometheus, RabbitMQ,
Redis, and TLS instead of generic simulator-only behavior.

## Contents

- `cases/`: all 14 repaired case packages.
- Source staging run: `runs/e2e/repair-14-fidelity-20260904` in the factory
  workspace.
- The package IDs are prefixed with `repair-` and retain their primitive and
  variant identity.

## Validation status at upload time

- Static package validation: 14/14 passed.
- Docker runtime gate: 5/14 passed and published to the local candidate pool.
- One RabbitMQ case was attempted but hit host-level Docker infrastructure
  failures while another gate occupied the shared Docker daemon; the remaining
  cases were left pending for incremental retry.
- This is an expert-review repair snapshot, not a claim that all 14 cases have
  passed the Docker runtime gate.

The original compact cases and all existing benchmark content remain unchanged.
