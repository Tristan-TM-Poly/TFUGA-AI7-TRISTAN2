# Ω Meta-Theory Evolution R0.10 — Reprovenance & Replay

R0.10 is the n+1 falsifier after R0.9. It asks whether a policy or challenge mechanism remains credible across independently declared frozen slices, repeated runs, historical replay, and counterfactual replay before any further meta-layer is justified.

## Core loop

`IndependentFrozenSlices -> ProvenanceGraph -> LeakageDetection -> CrossRunReplay -> HistoricalReplay -> CounterfactualReplay -> PROMOTE/HOLD`

## New finite courts

- `provenance_independence`: detects declared shared provenance identities and benchmark/training identity leakage.
- `cross_run_reproducibility`: measures exact decision agreement over common frozen cases across declared runs.
- `historical_replay`: blocks unapproved changes to frozen historical decisions.
- `counterfactual_replay`: compares finite candidate-vs-baseline utility traces under a frozen utility definition.
- `r10_promotion_gate`: promotes only when every supplied court passes.

## OAK boundaries

- ProvenanceDisjoint != StatisticalIndependence.
- ReproducibleDecision != CorrectDecision.
- HistoricalPreservation != HistoricalOptimality.
- CounterfactualReplayPASS != RealWorldCausalBenefit.
- BenchmarkIdentityLeakageDetected is a guardrail, not a complete contamination detector.
- PROMOTE does not bypass GitHub, security, legal, human-review, or external authority gates.

## Saturation consequence

R0.10 is deliberately positioned as a closure test. If the finite courts pass and no new independently evidenced residual appears, the preferred outcome is `STOP/CRYSTALLIZE`, not automatic R0.11 creation.

A future layer is justified only by a concrete residual such as:

1. reproducibility failure under genuinely independent data;
2. provenance ambiguity the current identity graph cannot represent;
3. replay disagreement that cannot be explained by authorized policy change;
4. empirical evidence that the current leakage detector misses material contamination.

This turns `n+1` from endless depth into a falsification-backed stopping rule.
