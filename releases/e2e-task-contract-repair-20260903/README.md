# E2E task-contract repair snapshot

This snapshot contains the 23 selected case-family variants whose public task
opening was repaired to describe a case-specific observable symptom. The
Runtime, Verifier, and public tool contracts were not changed.

## Validation status

- Static package validation: **23/23 passed**.
- Docker runtime/control gate: **20/23 passed**.
- The three runtime-pending cases are retained here for expert review:
  - `dynamic-linux_conntrack_exhaustion_v1-v1-20260902-15` — public tool oracle
    agent did not complete.
  - `dynamic-postgres_replication_lag_v1-v1-20260902-27` — public tool oracle
    agent did not complete.
  - `dynamic-nginx_bind_conflict_v1-v1-20260902-63` — infrastructure failures
    in no-op, wrong-fix, and partial-fix controls.

This is a review snapshot, not an automatic benchmark promotion. The cases
are copied from the local validated pool after the task-text repair and are
kept separate from the existing 106-case evaluation snapshot.
