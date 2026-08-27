# Difficulty Design and Calibration

## Structural difficulty

The case manifest contains a deterministic difficulty contract. The five pilot
cases receive `hard`, score `8/10`, using:

- `diagnostic_uncertainty`;
- `signal_indirection`;
- `tool_breadth`;
- `repair_depth`;
- `verification_complexity`.

The score is derived from trusted IDs and rules. The model cannot raise the
score by declaring a task hard.

## Mechanisms used in this pilot

- a healthy process can coexist with a failed business operation;
- the root signal is in a live database, cache, or dependency state;
- repair uses a two-stage prepare/apply protocol;
- restart or lifecycle persistence is checked;
- no-op, wrong-fix, and partial-fix controls are required.

## Why the pilot is not empirically hard yet

GLM-4.7 solved all four runtime-ready cases in the standard evaluation budget.
The current tool layer exposes bounded diagnostics and registered repair
actions. This improves safety and reproducibility, but also reduces the Agent's
search space.

The correct interpretation is:

`runtime-valid: yes for 4 cases; structurally hard: intended, 8/10;
empirically hard: not demonstrated.`

## Recommended ways to increase difficulty

1. Add real, plausible distractor signals without inventing random noise.
2. Require two or more independent observations before a repair is identifiable.
3. Put the effective value in a configuration layer different from the stale
   base configuration.
4. Make a wrong-layer edit or one-time restart appear to recover briefly but
   fail after restart, reconciliation, or consumer rebalance.
5. Include several plausible repair actions, while allowing only one to satisfy
   business, root-cause, contract, and persistence checks.
6. Strengthen partial-fix controls: one holder, one partition, one cache field,
   or one dependency must not be enough to recover the whole task.
7. Add business, root-signal, persistence, contract, safety, and SLO checks;
   critical checks must all pass and cannot be hidden by an average score.
8. Create variants by changing at least two structural dimensions: parameters,
   state layers, observable signals, tools, repair depth, or checks. Text-only
   paraphrases are duplicates.
9. Calibrate with repeated weak/standard/strong Agent configurations. Do not
   manufacture difficulty by only shortening the timeout.

## Suggested calibration targets

```text
easy:   70%-100% success
medium: 35%-70% success
hard:   10%-40% success
```

Use a frozen manifest and repeat unstable or anomalous cases. A case should be
marked `empirically_calibrated` only after stable repeated results and clean
runtime controls.
