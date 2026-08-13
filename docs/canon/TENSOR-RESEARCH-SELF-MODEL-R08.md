# Ω-TENSOR-RESEARCH-SELF-MODEL-T∞ — R0.8

## Status

**Executable predictive software-model candidate, stacked on PR #443.**

R0.8 is deliberately downstream of R0.7 Tensor DiscoveryBench. It converts
benchmark/research episodes into a small empirical memory of which operators,
coalitions and architecture classes have been associated with useful outcomes.

It does **not** claim that observational history establishes causality, human
cognition, scientific truth, or external scientific productivity.

## Mother invariant

```text
history of outcomes != causal explanation of outcomes
```

The self-model may learn:

```text
P(outcome_proxy | problem family, architecture, coalition, operators)
```

but it may not silently promote that association into:

```text
P(outcome | intervention do(operator))
```

without an intervention design that justifies such a claim.

## ResearchEpisode

Every episode preserves:

- problem/family;
- system kind;
- selected logical PersonLLMT IDs;
- operator IDs;
- representation IDs;
- information-gain proxy;
- declared cost and declared risk;
- calibration proxy;
- hidden-target state;
- contamination-control state;
- outcome class;
- memory class;
- provenance;
- whether a genuine causal intervention existed;
- whether external scientific validation existed.

The deterministic seed maps the R0.7 surface into exactly:

```text
8 task families × 4 architecture kinds = 32 episodes
```

These are benchmark episodes, not 32 scientific discoveries.

## Append-only EpisodeLedger

The R0.8 ledger is append-only by contract. Duplicate episode IDs fail closed.

This preserves the distinction between:

```text
new evidence
and
rewriting old evidence
```

A future compaction layer may summarize history, but raw provenance must remain
recoverable.

## M+ / M- / M?

R0.8 explicitly keeps three memory states:

```text
M+  benchmark-useful evidence
M-  benchmark-negative evidence / anti-pattern
M?  unresolved evidence
```

Permanent boundaries:

```text
M+ != truth
M- != permanent refutation
M? must not be discarded merely because it is inconvenient
```

This makes uncertainty an explicit memory class rather than forcing every
observation into success/failure.

## Operator and coalition credit

For a unit U, R0.8 currently computes an observational association:

```text
CreditAssoc(U)
  = mean(information_proxy | U present)
  - mean(information_proxy | U absent)
```

Receipts carry:

```text
causal_credit_proven = false
confounding_possible = true
observational_only = true
```

This prevents a frequent research-self-model failure:

```text
operator occurred in successful paths
therefore
operator caused success
```

The same rule applies to coalition credit.

## PredictionReceipt

R0.8 predicts benchmark proxies from matching historical episode cells. Every
prediction states:

```text
predictive_association_only = true
causal_effect_proven = false
external_validity_proven = false
```

The deterministic fixture currently has one observation per
`BenchmarkFamily × SystemKind` cell. That is enough to test plumbing, not enough
to estimate a scientifically useful distribution.

Permanent M-:

```text
one benchmark cell != calibrated scientific model
```

## Value of Computation

R0.8 introduces a bounded policy proxy:

```text
VoC_proxy
  = expected_information_gain_proxy
  - expected_cost
  - risk_weight * expected_risk
  - uncertainty_weight * uncertainty
```

It is allowed to return either:

```text
recommend_compute = true
```

or:

```text
recommend_compute = false
```

A self-improving research system that cannot decide **not** to compute is not a
resource controller; it is only an expansion engine.

Every VoC receipt therefore preserves:

```text
policy_proxy_only = true
causal_effect_proven = false
guaranteed_positive_return = false
```

## Relation to GO MAX

R0.8 operationalizes a central GO MAX rule:

```text
maximize verified marginal gain per resource,
not raw number of branches, agents or tokens.
```

Conceptually:

```text
GO Gradient
  -> empirical episode history
  -> operator/coalition association
  -> Value of Computation
  -> compute / do-not-compute decision
```

This remains a software-policy approximation until calibrated on real tasks.

## Upstream dependency

R0.8 is a stacked candidate on the current R0.7 head. Its conclusions are not
promotable beyond software-contract status while upstream R0.6.1/R0.7 gates are
not green on the exact ancestry used by R0.8.

This is intentional:

```text
stacked development != upstream certification
```

## OAK acceptance gates

R0.8 is promotable as a software self-model layer only when:

1. Python 3.10–3.13 compile and targeted tests pass;
2. schema/runtime contracts align;
3. the deterministic ledger contains 32 unique episodes;
4. provenance is present for every episode;
5. the ledger rejects duplicate IDs;
6. M+, M- and M? remain distinct and all are exercised by the fixture;
7. operator credit remains observational/non-causal;
8. coalition credit remains observational/non-causal;
9. predictions never claim causal or external validity;
10. Value of Computation can recommend both compute and do-not-compute;
11. VoC never promises positive return;
12. benchmark history is not promoted to external scientific validation;
13. upstream R0.7 dependency remains explicit.

## Next falsifiable generation

Only after enough real or high-quality hidden benchmark episodes exist should a
future R0.8.x/R0.9 add:

- held-out calibration;
- Bayesian/posterior uncertainty over predicted outcomes;
- matched controls;
- randomized/interventional operator tests where feasible;
- Shapley-like coalition attribution with confidence intervals;
- contextual Value of Computation;
- nonstationarity / concept-drift detection;
- causal-credit receipts that are earned by design rather than asserted.

The intended trajectory is:

```text
R0.7 benchmark
-> R0.8 predictive self-model
-> intervention-aware credit
-> adaptive research policy
-> externally validated research compiler
```

not:

```text
benchmark correlation
-> autonomous intelligence claim
```

## Permanent doctrine

```text
prediction != causation
association credit != causal credit
M+ != truth
M- != permanent refutation
M? != garbage
VoC proxy != guaranteed return
benchmark history != external scientific validation
self-model != self-awareness
plus ultra = more calibrated and falsifiable
```
