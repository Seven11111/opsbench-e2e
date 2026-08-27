# E2E Generation Flow

## 1. Inputs

The pipeline accepts cleaned document records and source metadata. A case may
use one document or several compatible documents. Documents are retained for
provenance even when the selector excludes them from the active bundle.

The current pilot records source documents, annotations, bundles, candidates,
scenario specs, reviews, revisions, and reports under
`provenance/generation/<case-id>`.

## 2. Evidence and scenario construction

The evidence stage identifies claims such as symptom, impact, root cause,
repair, verification, constraints, and preconditions. Each claim points back to
an exact source span. The bundle is converted into a `ScenarioSpec`, containing:

- canonical task labels;
- component and fault primitive IDs;
- legal parameters;
- public task and allowed tools;
- expected success checks and negative controls;
- difficulty contract;
- evidence links and seed.

`EvidenceBundle` is a provenance and selection object. It does not mean every
document must be used. It prevents unsupported claims from silently becoming
public task facts and makes the generated case reproducible.

## 3. Trusted compilation

The renderer maps registered component and fault IDs to a complete case package.
It generates the Compose environment, runtime configuration, lifecycle scripts,
and verifier from trusted code. The current pilot does not let the generation
model write arbitrary Compose or verifier code.

This separation keeps images, versions, injection, verification, and cleanup
deterministic while rejecting host paths and Docker sockets.

## 4. Runtime gate

The normal lifecycle is:

`validate -> provision -> setup -> baseline_check -> inject -> check_injected ->
run_agent -> verify -> cleanup`.

The control gate additionally tests no-op, oracle, restart-only, wrong-fix,
partial-fix, repeat, and cleanup behavior. A case is not runtime-valid merely
because Compose starts; the injected fault and negative controls must behave as
specified.

## 5. Agent evaluation

The packaged ReAct Agent receives only `public/task.md`, `public/tools.json`,
runtime tools, and a writable trace directory. The evaluator runs the Agent in
the target container, then runs the hidden verifier outside the Agent's view.

The final result separates Agent completion, verifier task success,
infrastructure failures, timeouts, and cleanup failures.

## 6. Current pilot caveat

The five cases were built from registered trusted primitives using a
deterministic/offline candidate review path. GLM-4.7 was used for final Agent
evaluation. This release demonstrates runtime execution and provenance, but it
is not evidence that the generation model can autonomously produce calibrated
hard cases.
