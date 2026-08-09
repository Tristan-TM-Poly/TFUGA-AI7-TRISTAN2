# Ω-NEURO R0.4 — Verified External Bundle Adapter

R0.4 connects the fixed P1 tournament to local JSONL datasets without weakening the OAK boundary.

## Input pair

```text
data.jsonl
manifest.json
```

The manifest must satisfy `schemas/omega_neuro_dataset_manifest.schema.json`. The adapter recomputes SHA-256 over the exact `data.jsonl` bytes before parsing observations.

## Observation contract

Each JSONL row contains:

```json
{
  "sample_id": "unique observation identifier",
  "group_id": "experimental unit kept intact across train/test",
  "signal": 0.0,
  "address": "proximal|distal|other source-defined label",
  "context": 0.0,
  "target": 0.0
}
```

`sample_id` must be unique. `group_id` must represent the unit that must not leak across train/test boundaries: for example a cell, preparation, animal, participant, recording session, or other source-appropriate experimental unit.

## Fixed-analysis principle

R0.4 intentionally reuses the same nested P1 models and OAK penalties defined before external data are inspected:

```text
scalar
-> address_aware
-> address_plus_context
```

This reduces researcher degrees of freedom. If the model family, target, split rule, exclusions or preprocessing are changed after seeing the result, that change must produce a new analysis/version rather than silently replacing the old one.

## Provenance is not truth

The adapter distinguishes:

```text
hash match
    = exact payload identity

manifest says public/consented
    = provenance claim

source review
    = still required

predictive improvement
    = empirical signal candidate

causal/biological claim
    = requires stronger independent evidence
```

Accordingly every external report contains:

```json
{
  "provenance_review_required": true,
  "automatic_biological_promotion": false
}
```

This remains true even when the manifest says `public` or `consented` and the richer model wins.

## CLI

Without installing another entry point:

```bash
python -m omega_neuro_t.external_cli data.jsonl manifest.json --folds 5 --pretty
```

The command may also write a frozen report:

```bash
python -m omega_neuro_t.external_cli data.jsonl manifest.json --output reports/p1.json
```

## Required source-specific adapter work

A future adapter for a real neuroscience repository must document, at minimum:

- upstream dataset/release identifier;
- source URL or stable object identifier;
- exact license/access terms;
- citation;
- original experimental unit;
- mapping into `group_id`;
- mapping from raw measurements to `signal`, `address`, `context`, `target`;
- exclusions and missing-data policy;
- preprocessing steps and parameters;
- units;
- source-specific confounds;
- whether the target was defined before model inspection;
- independent reproduction route.

No source-specific mapping should be inferred silently.

## Safety / scope

R0.4 is research infrastructure. It is not a diagnostic pipeline and should not be used to infer an individual's neurological or psychiatric state, treatment need, or clinical prognosis.
