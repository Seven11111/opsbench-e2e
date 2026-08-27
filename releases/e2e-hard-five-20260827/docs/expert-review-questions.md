# Questions for Expert Review

## Task realism

- Does each symptom/impact pair resemble a real SRE or DevOps incident?
- Is the task objective clear without leaking the root cause?
- Are the prohibited shortcuts realistic and justified?

## Diagnostic difficulty

- Are the distractor signals plausible and sufficiently independent?
- Does the Agent need to combine multiple observations?
- Does the public tool protocol reveal too much of the answer?

## Repair and persistence

- Is the registered repair the smallest safe operational action?
- Can a wrong-layer edit, restart-only action, or caller-side workaround
  produce a false positive?
- Does the verifier test persistence at a meaningful lifecycle boundary?

## Verifier quality

- Does every critical user goal have a live-state check?
- Are partial and unsafe repairs rejected?
- Are all score weights normalized and is `passed` independent of a misleading
  weighted average?

## Dataset diversity

- Are variants materially different in fault parameters, state layers, signals,
  tool paths, repair depth, or verification requirements?
- Are different document sources and technology versions represented?
- Is the easy/medium/hard mix supported by repeated Agent-panel evidence?

## Release policy

- Should the four runtime-ready cases remain pilot/regression cases or enter a
  development benchmark?
- What additional runtime evidence is required before a primitive becomes
  calibrated?
- How should Kafka consumer-group lifecycle failures be isolated from Agent
  failures in future reports?
