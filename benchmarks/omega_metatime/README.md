# Ω-METATIME matched baseline benchmark

This benchmark is a protocol, not evidence of superiority.

## Objective

Measure whether Ω-METATIME reduces time-to-capability without degrading retention, transfer or calibration relative to a conventional study/build workflow.

## Frozen task design

Choose one bounded task with:
- a public specification or course-level objective,
- fixed allowed resources,
- a pre-registered completion rubric,
- a fixed test set not used while building,
- no changing success criterion after seeing results.

Recommended first task: one small engineering/physics concept plus one implementation task whose outputs can be graded independently.

## Two conditions

### Baseline
Conventional workflow: read/learn, solve exercises, implement, test, review.

### Ω-METATIME
Use TemporalCounters, regime control, branching budget, StrategyGenome tournament, proof-bandwidth gating, crystallization and regeneration.

## Measures

Record for both conditions:
- active minutes/hours,
- completion score on frozen test,
- verified capability units,
- immediate calibration,
- 7-day retention,
- 30-day retention,
- near transfer,
- far transfer where feasible,
- number of claims produced,
- number of claims verified,
- Proof Bandwidth,
- complexity/debt introduced,
- reusable artifacts,
- regeneration closure.

## Speedup rule

Only compute

`speedup = baseline_hours / omega_hours`

when Ω-METATIME is non-inferior on retention, transfer and calibration under the pre-registered thresholds. Otherwise the result is `NOT VALIDATED`.

## Anti-bias requirements

- freeze the rubric first,
- keep holdout tests hidden from the strategy generator when possible,
- record failures and abandoned branches,
- do not discard slow Ω-METATIME trials,
- do not compare unlike tasks,
- do not convert self-report into measured mastery,
- repeat before generalizing.

## Promotion criterion

R0.1 may be promoted only after repeated evidence that its gain exceeds the added attention, complexity, compute, risk and epistemic debt. A null result or simpler-baseline win should trigger merge/prune rather than rationalization.
