# Ω-META-THEORY-EVOLUTION R0.9 — Shift, Calibration, Ablation, Saturation

R0.9 executes the next falsifier after R0.8. A challenge process that looks informative on one candidate population and under one proxy may fail when the candidate population moves, when the proxy is compared with realized gains, or when challenge families are ablated.

## Core laws

```text
CandidatePopulationStable != CandidatePopulationShifted
DiscriminationProxy != RealizedVerifiedGain
ChallengePresent != ChallengeNecessary
MoreChallenges != MoreVerifiedInformation
```

## Population shift

`candidate_population_shift(...)` measures finite identity-level overlap between the reference and shifted candidate populations. Low declared Jaccard overlap yields HOLD.

This is deliberately weaker than a distributional test: identity overlap is only a shift signal.

## Proxy calibration

`calibrate_information_proxy(...)` compares predicted discrimination/information values against later realized verified gains. It reports mean absolute error, signed bias and maximum absolute error. Insufficient samples or excessive declared MAE yield HOLD.

The R0.8 proxy `4p(1-p)` remains a discrimination heuristic, not Shannon information without a probability model.

## Challenge ablation

`challenge_family_ablation(...)` evaluates the candidate verdict signature under all frozen challenge families, then removes each family in turn. A family receives finite discriminative credit only when removing it reduces the number of distinct candidate signatures.

This prevents challenge accumulation without demonstrated discriminative contribution.

## Adaptive saturation

`adaptive_information_stop(...)` uses a declared recent window of verified-gain observations.

- recent mean gain below threshold -> `STOP`;
- recent mean gain at/above threshold -> `CONTINUE`;
- insufficient history -> `HOLD`.

`STOP` means only that the supplied recent trace is below the declared marginal threshold. It does not prove that no future useful challenge exists.

## OAK boundaries

- PopulationOverlap != DistributionalEquivalence.
- ProxyCalibrationPASS != UniversalCalibration.
- AblationContribution != SemanticNecessity.
- AdaptiveSTOP != DiscoveryExhausted.
- FinitePASS != UniversalTruth.
- The evaluator and success criteria remain external/frozen relative to the system-under-test.

## Anti-inflation

Exactly four new surfaces: implementation, tests, canonical specification and CI. R0.9 reuses R0.8/R0.7/R0.6/R0.5/R0.4.

## n+1 residual

If R0.9 survives, the next useful falsifier is cross-run reproducibility and provenance independence: repeat the same challenge-selection/calibration decision under independently sourced frozen slices, detect benchmark leakage or shared hidden provenance, and compare policy performance under historical/counterfactual replay before any further meta-layer is promoted.
