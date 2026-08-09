# R0.6 — Public-data preregistration

## Status

**D/X — protocol and source registry implemented; no public-data biological result claimed.**

R0.6 freezes the source-selection and evaluation rules that must exist **before** P1/P2/P3 are measured on external neuroscience data.

The central invariant is:

```text
source discovery
-> source/version/license review
-> protocol freeze + SHA-256
-> asset acquisition + payload hash
-> leakage-safe grouping
-> frozen baseline/candidate tournament
-> ablations + negative controls
-> OAK report
-> external-condition reproduction
-> only then consider claim promotion
```

A score can validate software or support an empirical inference. It cannot automatically promote a biological claim.

## Primary source registry

### Allen Cell Types Database

Official documentation: `https://brain-map.org/support/documentation/cell-types-database-api`

R0.6 role:
- P1 Dendritic Address candidate source;
- P2 state-model candidate source where variables are actually observable;
- future P4 Morphology–Computation source.

The official API exposes single-cell metadata, electrophysiology in NWB, morphology reconstructions in SWC for a subset of cells, computed features and neuronal models. R0.6 freezes specimen/file identifiers and hashes every acquired payload rather than treating the API endpoint alone as a dataset version.

Important limitations:
- morphology is not available for every specimen;
- mouse and human records require explicit species/donor handling;
- somatic current-injection data do not directly reveal arbitrary synapse-level latent state;
- availability of a feature does not make it causal.

### MICrONS cubic-millimeter functional connectome

Official portal: `https://www.microns-explorer.org/cortical-mm3`

R0.6 role:
- primary P3 Higher-Order Wiring source;
- future P5 Dynamic Connectome candidate;
- possible P7 glial/higher-order work only when the required entities are actually represented and justified.

The resource combines electron-microscopy reconstruction/connectivity with functional two-photon measurements in the same cortical volume. R0.6 records the materialization/data-release identifier, exact table names and query, root IDs, coregistration provenance and export hashes.

Important limitations:
- the cubic-millimeter resource comes from one mouse, so it cannot establish population universality by itself;
- manually verified and automatic coregistration tables have different confidence levels;
- segmentation/proofreading state changes over time, therefore materialization/version must be frozen;
- motifs must be defined without target leakage.

Preferred confirmation for structure↔function tests uses manually verified coregistration when sample size permits, with automatic matches treated as a separate sensitivity analysis rather than silently pooled evidence.

### DANDI / NWB

Official documentation: `https://docs.dandiarchive.org/introduction/`
API documentation: `https://docs.dandiarchive.org/api/rest-api/`

R0.6 role:
- standardized/versioned public neurophysiology source layer;
- candidate P1/P2/P5/P6 source depending on the selected Dandiset.

DANDI contains versioned Dandisets and supports NWB for neurophysiology. Public data can be accessed programmatically. R0.6 requires a **published version** for evidence claims when possible and freezes `dandiset_id + version + asset_id/contentUrl + payload hash`.

Important limitations:
- DANDI is an archive, not one homogeneous experiment;
- licenses and variables are Dandiset-specific;
- draft Dandisets are mutable;
- a dataset must satisfy the hypothesis-specific variable and grouping contract before admission.

## Frozen protocols

The executable protocols live in `omega_neuro_t/r06_protocol.py`.

Each `FrozenEvaluationProtocol` records:
- hypothesis ID;
- source priority;
- target definition;
- group-key policy;
- baseline family;
- candidate family;
- metrics;
- ablations;
- negative controls;
- confounds;
- split policy;
- minimum external-condition requirement.

Canonical JSON is hashed with SHA-256. If any semantic field changes, the protocol hash changes.

This is the R0.6 anti-moving-goalpost invariant:

```text
protocol_before_data.hash != modified_after_results.hash
```

A changed protocol is allowed, but it becomes a new registered analysis and must not be represented as the original preregistration.

## P1 — Dendritic Address

Primary source priority:
1. Allen Cell Types;
2. suitable published DANDI datasets.

Baseline:
- electrophysiology/cell-level covariates without dendritic morphology.

Candidate:
- same baseline plus preregistered morphology/address descriptors.

Negative control:
- permute morphology/address labels within admissible strata.

Core confounds:
- species;
- donor;
- cell type;
- cortical layer;
- recording protocol;
- morphology availability/selection.

The first external P1 experiment should therefore test whether morphology/address variables add held-out predictive information after these controls. It must **not** claim that the current Allen recordings experimentally manipulate synaptic dendritic address.

## P2 — Synaptic State Tensor

Primary source priority:
1. suitable DANDI experiment with state dimensions measured before target observation;
2. Allen only for narrower state-model tests actually supported by available measurements.

Baseline:
- one scalar state proxy.

Candidate:
- multidimensional observed state representation.

Negative control:
- permute state/context dimensions within admissible experimental strata.

P2 is intentionally source-sensitive: R0.6 rejects any attempt to infer an unobserved rich synaptic tensor merely because a dataset is neuroscientific.

## P3 — Higher-Order Wiring

Primary source:
- MICrONS cubic-millimeter dataset.

Baseline:
- pairwise strength/degree/recurrence descriptors.

Candidate:
- order-3/order-4 motif descriptors plus preregistered context interactions.

Negative control:
- permute motif assignments while preserving admissible degree/context strata.

Core confounds:
- cell type;
- cortical area;
- depth;
- proofreading state;
- coregistration confidence;
- materialization version.

The target must be defined independently of the motif-construction procedure. Otherwise the campaign is rejected for target leakage.

## Admission gate

`admission_gate(hypothesis_id, source_id)` does not download or bless data. It records that the source class is eligible for **data preparation** under the frozen protocol.

Every admitted asset still requires:
- exact asset/release/version identifiers;
- license review;
- citation/provenance review;
- payload SHA-256;
- variable mapping;
- group-key mapping;
- missingness audit;
- leakage audit;
- negative control;
- no automatic biological promotion.

## Commands

```bash
python -m omega_neuro_t.r06_cli --pretty
python -m omega_neuro_t.r06_cli \
  --hypothesis P3_HIGHER_ORDER_WIRING \
  --source microns_mm3 \
  --pretty
python -m pytest tests/test_omega_neuro_r06.py -q
```

## R0.6 completion gate

R0.6 is complete only when at least one external asset bundle has:
1. immutable/frozen source identifiers;
2. reviewed license/citation metadata;
3. verified payload hashes;
4. mapped variables and group keys;
5. protocol hash captured **before** evaluation;
6. baseline/candidate/ablation/negative-control results;
7. residual and uncertainty report;
8. explicit failure cases in M-minus;
9. reproduction on at least one external condition if the claim scope requires it.

Until then the status remains **public-data preregistration / adapter engineering**, not neuroscience validation.
