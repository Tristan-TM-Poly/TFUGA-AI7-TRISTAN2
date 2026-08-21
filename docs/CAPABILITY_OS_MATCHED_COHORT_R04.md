# Ω-CAPABILITY-OS Matched Cohort R0.4

## Mission

Advance the prospective measurement court from raw cohort means to exact declared matching, uncertainty-aware effect estimates, and a sequential HOLD/PROMOTE/STOP rule.

```text
ProspectiveExecutionReceipt
→ exact declared strata matching
→ paired metric deltas
→ normal-approximation uncertainty interval
→ finite non-inferiority / improvement gate
→ HOLD | PROMOTE | STOP
```

## Reuse-first

R0.4 reuses `FrozenMeasurementCriteria` and `ProspectiveExecutionReceipt` from R0.3. It does not create a second telemetry or capability ontology and it does not invent a future receipt dataset.

## Exact matching

Default matching keys are:

- `task_family`
- `difficulty_band`
- `risk_band`

Missing strata fail closed. Exact equality of those labels is only a declared comparability proxy.

```text
ExactStrataMatch != EqualDifficulty
MatchedCohort != RandomizedTrial
```

## Uncertainty and effect size

For each frozen lower-is-better metric, R0.4 computes paired deltas:

```text
delta_i = transplant_i - baseline_i
```

and reports the mean delta, standard error, a configurable normal-approximation interval, and a paired standardized effect when the paired standard deviation is non-zero.

The interval is an engineering approximation, not an exact small-sample theorem and not a causal confidence guarantee.

## Sequential decision

Before evaluation, `SequentialCriteria` freezes:

- `min_pairs`
- `max_pairs`
- `z_value`
- `noninferiority_margin`
- whether strict improvement is required.

Rules:

```text
pair_count < min_pairs -> HOLD
all upper bounds <= noninferiority_margin
AND at least one upper bound < 0 when strict improvement is required
AND no authority widening / criteria mutation
-> PROMOTE
```

If the court still cannot clear the frozen conditions at `max_pairs`, it returns `STOP` rather than silently changing the criteria.

```text
MoreSamples != GuaranteedPromotion
EvaluationMutation != Repair
```

## OAK boundaries

```text
Prospective != Randomized
ExactStrataMatch != MatchedDifficulty
NormalApproximationInterval != ExactConfidenceGuarantee
StandardizedEffect != CausalEffect
FiniteNonInferiority != UniversalImprovement
STOP != ProofOfNoEffect
PROMOTE != ExternalActionAuthority
CI green != ExternalWorldTruth
```

## Next evidence frontier

Do not add a broader statistical layer until real prospective receipts accumulate. The next justified move is to ingest actual execution receipts under the frozen R0.3/R0.4 contracts and inspect whether matching coverage, uncertainty and effect estimates remain informative on real new work.
