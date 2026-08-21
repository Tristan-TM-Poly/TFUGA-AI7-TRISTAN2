# Ω-CAPABILITY-OS Prospective Measurement R0.3

## Mission

Move from retrospective replay to pre-registered engineering measurement.

```text
freeze criteria
→ execute baseline/transplant cases
→ emit ProspectiveExecutionReceipt
→ compare fixed lower-is-better metrics
→ PROMOTE | HOLD
```

The frozen metrics are repair iterations, CI failures, persistent changes, regressions, tool calls, residuals remaining, and seconds to GlobalPASS.

## Hard rule

Criteria are hashed before scoring. A receipt whose `criteria_digest` differs from the frozen criteria is rejected. Evaluation criteria therefore cannot be changed retroactively to make an observed execution pass.

## Promotion court

By default, the transplant cohort must be non-inferior on every frozen metric and strictly improve at least one. Any implicit authority widening blocks promotion independently of metric gains.

## OAK boundaries

```text
Prospective != Randomized
MatchedCriteria != MatchedDifficulty
LowerMean != CausalBenefit
NonInferiorFiniteCohort != UniversalImprovement
GlobalPASSTime != ScientificTruth
FewerToolCalls != BetterOutcome
PROMOTE != ExternalActionAuthority
```

R0.3 creates the instrumentation and frozen court now. It does not fabricate future observations. Real causal-strength claims require actual prospectively collected comparable executions, sufficient cohorts, and stronger assignment/matching where feasible.

## Saturation rule

Do not create another generic layer merely because R0.3 exists. The next promotion must be earned by real receipts produced under frozen criteria. If measured deltas are zero, mixed, or regressive, HOLD or simplify the transplant.
