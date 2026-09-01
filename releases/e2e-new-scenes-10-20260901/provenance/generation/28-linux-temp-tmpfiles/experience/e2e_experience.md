# Shared Generation Experience

These are prompt-level generation rules, not model training data.

- Keep all claims grounded in the supplied evidence bundle.
- Do not invent a Compose file, injection script, verifier, or technology that is not selected by a trusted template.
- Prefer one observable user goal and a deterministic verification signal.
- Reject evidence conflicts instead of silently choosing one source.
- Keep provenance references attached to every generated candidate.


---

# E2E Review Experience e2e-v1

This file is a versioned prompt-level review knowledge base. It is read by the
E2E candidate extractor and is not used to update model parameters.

## Keep

- Expose symptoms and impact, while requiring the agent to discover the operational root cause.
- Make the repair observable through a live state, service signal, or trusted verifier check.
- Use the smallest repair that restores the documented service contract.

## Avoid

- Do not expose hidden scenario fields, verifier implementation details, or the exact expected configuration in the public task.
- Do not accept a candidate whose repair cannot be rendered by a trusted template.
- Do not treat an agent's final explanation as proof of success.
- Do not make a verifier require an implementation detail that is absent from the public objective or source evidence, such as an arbitrary resource name.
- Do not derive correctness from the oracle's chosen identifier when multiple semantically equivalent repairs preserve the service contract.

## Open conflicts

- New template-specific rules require human review before release.
- A verifier false negative must be classified against the task contract before changing the case: preserve genuine Agent failures, but repair evaluator-only constraints that reject a valid contract-preserving action.

## Global task–tools–verifier contract (e2e-alignment-v1)

- Treat the public task, public tools, and hidden verifier as one contract. The task
  states user-visible outcomes; tools expose concrete ways to observe and change
  the allowed state; the verifier checks those same outcomes.
- Every verifier obligation that matters to success must have a corresponding
  natural-language success signal in the public task. Do not require a hidden
  implementation detail, arbitrary filename, private PID, marker, or exact
  internal identifier that the user was never asked to preserve.
- Every declared repair operation must be executable through at least one public
  tool. A tool description must state its scope, inputs, observable result, and
  safety boundary. “Use it”, “fix the service”, and similarly vague descriptions
  are invalid.
- Public tool names may be concise (no more than three words) and related to the
  capability, but must not contain the fault name, exact answer, secret key, or
  an oracle-specific operation. Prefer names such as `config read`, `config
  update`, `service status`, `business probe`, or `service restart`.
- A case is not publishable merely because an oracle can pass it. The normal
  public task must make the verifier's meaningful checks reachable without
  revealing the hidden repair. No-op, wrong-layer, partial, and restart-only
  controls must fail for the same semantic reason that the task is considered
  unfinished.
- Public does not mean that the task states the exact answer. A key verifier
  condition must be reasonably inferable from the task, public tool returns,
  the healthy baseline, the reference documentation, or a generic safety
  constraint. Keep the root cause and exact repair hidden when exploration is
  part of the task, but never make success depend on an undiscoverable fact.
- Separate the contract shown to the Agent (goal, observable signals,
  available capabilities, and public invariants) from the evaluator contract
  (repair classes, check mapping, valid/invalid solution sets). Never place the
  latter in public/task.md or public/tools.json.
- Domain tools are allowed when they expose bounded, discoverable capabilities:
  session listing, queue inspection, cache read/write, target description, and
  lifecycle control are acceptable. A tool must not require a hidden literal
  such as `recover_dependency` or `apply_expected_solution`; dynamic IDs must
  come from prior observations and closed operations must use an enum or a
  capability-discovery response.
- An internal state file is valid only when it causally drives later runtime
  behavior and its effect is observable. Do not score a case from a private
  ledger, marker, exact PID, or file-existence artifact that has no effect on
  the business operation.
- Define expected outcomes per runtime control. Restart-only normally fails,
  but it may pass for a genuinely transient fault when the case records the
  reason. If multiple safe repair classes exist, test at least two; otherwise
  record why a single oracle is sufficient. Symptom-only and constraint-
  breaking repairs must remain negative controls.
- Verifier scores are diagnostic only: all critical checks must be conjunctive,
  the check weights must sum to 1.0, and an all-pass result must have score
  1.0. A partial score must never promote an incomplete repair.
- When a review or runtime check fails, feedback must distinguish observed facts
  from hypotheses and include the exact field/file, likely cause, required change,
  forbidden workaround, and a concrete re-test condition. Carry every previous
  feedback item and artifact version into the next repair round.

## Fairness repair lessons (e2e-contract-alignment-v2)

These rules were distilled from timeout-SLO and stale-PID review. They are
general generation constraints, not case-specific answers.

- Derive the public task, public tools, runtime oracle, and verifier from one
  explicit contract. A verifier must not check a second threshold, exact file,
  private action label, or ledger field that is absent from that contract.
- Every numeric value that can change a pass/fail decision must have a recorded
  provenance: public task objective, public tool result, documented runtime
  contract, or a clearly named protocol constant. Do not put an extra safe
  value in the verifier merely because it makes one implementation pass.
- If a latency objective is public, use that one objective for request latency,
  dependency delay, and timeout-policy checks. Report the value in probe details
  so a reviewer can audit the decision. Do not combine a public budget with a
  hidden lower delay cutoff.
- Lifecycle repair tools must use generic capability names and closed enums.
  Service identifiers, source identifiers, and other dynamic parameters must
  come from an observation tool. Never require a primitive-specific string such
  as `restore_service_identity` or `recover_dependency`.
- A public oracle is only a reachability test. It must discover the target,
  observe the failing state, call the same public capability exposed to the
  Agent, and verify the semantic outcome after the lifecycle boundary. It must
  not call a hidden action or private runtime script.
- When more than one contract-preserving repair is plausible, include at least
  two positive controls (for example restart and stop/start) and make their
  expected outcomes explicit. Negative controls should fail for the same
  semantic reason as the user task, not because they missed a hidden literal.
- Before release, run a transitive provenance lint over the verifier and public
  oracle path. Reject hidden action literals, undeclared decision thresholds,
  and checks that depend only on a non-causal state file. Keep all previous
  review feedback and runtime evidence in the next repair prompt.

## Baseline contract lessons (e2e-contract-alignment-v3)

These rules come from the HTTP timeout regression and apply to every future
trusted renderer and dynamically generated case.

- Validate the healthy baseline against the same public contract used after
  repair. A case must not become invalid merely because the verifier was made
  stricter during a fairness fix.
- Any public SLO must have a healthy baseline value inside its declared budget;
  injection may violate that budget, while the oracle must restore it. Render
  baseline configuration and public SLO from the same contract source.
- If a verifier adds a new critical check, update the baseline fixture,
  injection logic, oracle controls, public tool output, and static alignment
  tests together. Do not patch only the verifier.
- Record the contract value and its origin in runtime probe details so a failed
  baseline can be diagnosed as a case-design mismatch rather than an Agent
  failure.

## Release fairness lessons (e2e-contract-alignment-v4)

These rules come from the HTTP retry/circuit-breaker, Kafka lag, and
PostgreSQL pool reviews. They apply to all future generated E2E cases.

- A repair action is fair only when the Agent can discover or select it from
  the public contract. Do not require a hidden literal such as
  `recover_dependency`, `rebuild_cache_payload`, or
  `release_pool_holders`. Prefer generic tools with observable parameters:
  `config_update(operation=set/remove)`, `service_manage(action=restart)`, or
  a closed enum returned by a prior observation tool.
- `check_injected.py` must prove the public symptom, not just an internal
  flag. If the task says an endpoint returns 503, a query fails, lag grows, or
  a catalog payload is invalid, the injected-state check must observe that
  live behavior directly.
- The public task threshold and verifier threshold must be the same value. A
  task that says "lag below five messages" cannot secretly require `lag <= 2`.
  Every pass/fail threshold must appear in the public task, public tool output,
  or manifest threshold provenance.
- A verifier must not require `state["mode"] == "baseline"` or similar private
  ledger values as the success predicate. Internal state may drive the fault,
  but final correctness should be checked through business behavior,
  root-cause signals, and persistence after the lifecycle boundary.
- Backlog, queue, circuit-breaker, and pool cases must include bypass controls:
  stopping workload permanently, clearing a symptom without restoring the
  service contract, editing a state ledger directly, and partial repair should
  all fail.
- A passing case is not automatically a good hard case. If the task text tells
  the Agent to perform the exact prepare/apply repair sequence, classify it as
  answer leakage and rewrite the task to expose symptoms, impact, constraints,
  and public success criteria only.


---

# E2E Fairness and Task Contract Experience

Version: `e2e-fairness-v1`

This is a prompt-level review knowledge base. It is loaded by the generator
and Judge; it is not model training data or model parameters.

## Public inferability

The public task may be operationally incomplete and may require diagnosis. It
must still make every critical success condition reasonably inferable from at
least one public source: task wording, public tool output, healthy baseline,
reference documentation, or a generic safety invariant. Do not put the exact
root cause, configuration layer, action label, threshold, or expected file
name in the task merely to make the verifier fair.

## Contract split

The Agent-visible contract contains only:

- the business goal;
- observable symptoms and signals;
- available bounded tools;
- public invariants such as preserving the service contract and unrelated data.

Keep these evaluator-only fields private:

- allowed repair classes;
- verifier check mapping;
- known valid and invalid solutions;
- exact fault parameters and control commands.

## Tool rules

Tool names should be concise capability names of at most three words and may be
domain-specific when their function is clear. A tool may accept an object ID
only when that ID is returned by a preceding observation. Closed operations
must use a public enum or a capability-discovery result. Never require a hidden
string such as `recover_dependency`, `rebuild_cache_payload`, or
`apply_expected_solution`.

## Verifier rules

Judge outcomes and runtime controls must test semantic business behavior,
root-signal absence, safety invariants, and persistence where persistence is a
publicly inferable requirement. A state file or ledger may be checked only when
the service reads it and changing it changes later observable behavior. A
weighted score is explanatory; `passed` is conjunctive and all passing checks
must produce `score: 1.0`.

## Control rules

Use no-op, oracle, wrong-fix, partial-fix, repeat, and restart-only when they
are meaningful for the primitive. Store `expected: pass|fail` and a reason per
control. Do not assume restart-only always fails. If two safe repair paths are
plausible, validate two; if only one is safe, document why one oracle is enough.

## Feedback format

Every rejection must state: the observed fact, likely cause, exact field/file,
required change, forbidden workaround, and a concrete re-test condition. Carry
all prior feedback and artifact versions into the next repair prompt.
