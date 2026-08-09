# Roadmap — Ω-NEURO-CELL-SYN-NET-T∞

## R0.1 — executable hypothesis kernel

Deliverables in this PR:

- typed cell, branch, synapse, hyperedge and network states;
- explicit epistemic statuses;
- dendritic address-aware reference integration;
- scalar vs contextual synapse projections;
- LOG/EXP plasticity reference update;
- multilayer higher-order relation model;
- OAK predictive/complexity/uncertainty score;
- synthetic specialized-network fingerprints;
- deterministic CLI demo;
- unit tests for invariants and OAK behavior;
- P1–P7 falsification contracts.

Promotion target: **D-MVP as software**, while the biological hypotheses remain X/E until external evidence is ingested and benchmarks run.

## R0.2 — evidence adapters

Add provenance-preserving adapters for public, appropriately licensed neuroscience resources. Do not hard-code biological claims into the kernel.

Common normalized contracts should support, when available:

- multimodal cell metadata;
- morphology/reconstruction features;
- electrophysiological response features;
- synapse/connectivity observations;
- signal time series;
- spatial/experimental covariates;
- source/version/license/provenance.

Outputs:

```text
generated/omega_neuro_t/<dataset>/
  manifest.json
  cells.jsonl
  relations.jsonl
  features.jsonl
  evidence-ledger.jsonl
  oak-report.json
  m-minus.jsonl
```

No dataset is treated as universally representative of all species, regions, preparations or states.

## R0.3 — P1/P2 benchmark wave

First empirical targets:

1. P1 address-aware vs address-agnostic prediction;
2. P2 scalar synapse vs state-tensor prediction.

Required:

- leakage-safe split;
- matched-capacity controls;
- ablations;
- uncertainty;
- residual plots/reports;
- deterministic seeds where stochastic algorithms are used;
- machine-readable promotion decisions.

## R0.4 — P3/P4 topology + morphology wave

Build pairwise and higher-order representations from the same source observations. Compare:

```text
pairwise only
pairwise + geometry
pairwise + geometry + higher-order motifs
```

For morphology:

```text
cell identity/covariates baseline
+ simple morphology
+ multiscale/topological invariants
```

Every improvement must survive a complexity-aware OAK gate.

## R0.5 — P5 dynamic network layers

Introduce time/context indexed layers:

```text
G_structural
G_effective(t)
G_plastic(t)
G_modulatory(t)
G_metabolic(t)
```

and evaluate whether a contracted `G_active(t)` improves prediction over structural connectivity plus node state.

## R0.6 — P6 multiscale signal lab

Benchmark task-appropriate standard signal representations before Tristan extensions. Candidate ladder:

```text
raw/statistical
-> Fourier/STFT
-> wavelet
-> validated multiscale baselines
-> FFWT candidate
-> FFWT + CVCD candidate
```

A Tristan transform is retained only when gains survive dimensionality matching, noise sweeps, hyperparameter controls and an external condition/dataset.

## R0.7 — P7 glial/context layer

Add measured context variables only for tasks/datasets where they exist and are interpretable. Compare neuronal-only and augmented models. Reject universalization from one preparation.

## R1 — NeuroHGFM evidence compiler

Target architecture:

```text
raw data + metadata
  -> provenance manifest
  -> CellGraph / SynapseGraph
  -> multimodal typed hypergraph
  -> invariant extraction
  -> model family generation
  -> OAKBench
  -> evidence + residual ledger
  -> M+/M-
  -> smallest reproducible promoted representation
```

## R2 — uncertainty and negative memory

Integrate Ω-UNC²-T principles:

- source uncertainty;
- measurement uncertainty;
- model uncertainty;
- calibration drift;
- confidence debt;
- residual-of-residual tracking;
- unknown-unknown flags;
- explicit M⁻ failed hypotheses/feature families.

## R3 — constrained model discovery

Only after empirical benchmark infrastructure exists:

- generate candidate state tensors and hyperedge vocabularies;
- search representations under hard complexity budgets;
- preserve simple baselines in every tournament;
- require out-of-sample reproduction before promotion;
- archive attractive but non-generalizing structures.

## OAK stop conditions

Stop expansion and return to evidence when any of these occurs:

- vocabulary grows faster than executable tests;
- new dimensions lack measurable definitions;
- predictive gain disappears after ablation;
- results depend on leakage or one fragile split;
- uncertainty exceeds the claimed effect;
- a causal statement is inferred from correlation alone;
- a clinical interpretation exceeds validated scope.

## North-star metric

Not maximum module count. The target is:

```text
minimum reproducible representation
that preserves the maximum task-relevant predictive information
with explicit residuals, uncertainty and provenance.
```
