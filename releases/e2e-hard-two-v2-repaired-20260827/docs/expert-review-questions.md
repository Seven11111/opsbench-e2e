# Expert Review Checklist

Please review the two cases and the generation/evaluation evidence using the
following checklist.

## Case realism

- Is the incident mechanism plausible in a real PostgreSQL/Redis deployment?
- Are the distractors operationally meaningful?
- Does the task preserve a realistic service contract and safe-remediation
  boundary?

## Solvability and difficulty

- Can an experienced operator infer the repair from public observations?
- Is the number of required diagnostic steps appropriate for a hard task?
- Does restart-only or direct symptom repair correctly fail?
- Are the cases too easy because the effective configuration is directly
  exposed?

## Verifier quality

- Does each verifier check business recovery, root-cause disappearance, and
  persistence?
- Are negative controls strong enough to catch shortcuts?
- Are the repeat and cleanup guarantees adequate?

## Benchmark validity

- Should these cases enter a benchmark after runtime validation, or require
  document provenance and Agent-panel calibration first?
- Which dimensions should determine empirical difficulty?
- What additional variants would provide meaningful diversity without merely
  changing wording?
