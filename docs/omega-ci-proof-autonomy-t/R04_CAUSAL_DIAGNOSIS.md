# Ω-CI-PROOF-AUTONOMY-T∞² R0.4 — Causal Diagnosis

R0.4 adds a finite and deterministic diagnostic layer above the R0.3 epistemic graph.

## Pipeline

```text
failure
→ concurrent causal hypotheses
→ finite observations
→ normalized heuristic support
→ entropy and information gain
→ discriminating experiment plan
→ minimal reproduction
→ bisect plan
→ counterfactual worlds
→ causal dossier for human review
```

## Epistemic boundary

A leading hypothesis is not a proven cause. Support scores are relative to the declared hypothesis set, priors, likelihoods and observation reliability. Unmodeled causes and interactions can remain.

Every diagnosis and dossier declares:

- `causality_proven: false`;
- `human_review_required: true`;
- `automatic_patch_allowed: false`;
- `automatic_merge_allowed: false`;
- `maximum_authority: A3`;
- `remote_mutations: 0`.

## Components

- `CausalDiagnosticEngine`: model-relative support update and ambiguity detection.
- `DiscriminatingExperimentPlanner`: expected entropy reduction per bounded cost.
- `DeltaMinimizer`: deterministic ddmin-style reduction for local finite fixtures.
- `BisectPlanner`: computes the next midpoint without invoking Git.
- `CounterfactualProjector`: records predicted outcomes under explicit interventions.
- `CausalDossierBuilder`: aggregates receipts without authorizing execution.

## Non-goals

R0.4 does not implement autonomous patches, branch writes, remote experiments, causal discovery from arbitrary repositories, scientific causality, or automatic merge.
