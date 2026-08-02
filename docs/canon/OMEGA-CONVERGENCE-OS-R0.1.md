# Ω-CONVERGENCE-OS R0.1

## Purpose

Ω-CONVERGENCE-OS converts a complex branch into a deterministic, inspectable convergence packet before any merge.

```text
branch/files/claims/workflows
→ Branch DNA
→ conflict analysis
→ dry-run merge plan
→ required gates
→ immutable receipt
→ human-authorized Git action
```

R0.1 is an analyzer and compiler. It does not fetch credentials, push branches, merge pull requests, deploy systems, publish claims, or authorize scientific promotion.

## Core objects

### Branch DNA

A Branch DNA records:

- base and head commit identifiers;
- changed paths, digests, sizes and binary status;
- public Python symbols;
- CLI entry points;
- GitHub Actions permissions;
- epistemic statuses;
- declared claims, tests and risks.

Its canonical JSON is sorted and hashed with SHA-256.

### Conflict tensor

R0.1 classifies conflicts as:

- file;
- API;
- dependency;
- schema;
- epistemic;
- policy;
- resource;
- binary.

The current executable analyzers cover Python public APIs, project scripts, workflow permissions, epistemic status promotion, same-path content divergence and binary preservation.

### Merge plan

Each changed path receives a strategy such as:

- `additive_overlay`;
- `semantic_three_way_merge`;
- `semantic_merge_with_compatibility_adapter`;
- `version_schema_and_add_migration`;
- `separate_status_dimensions_and_require_evidence`;
- `preserve_blob_then_select_by_sha`;
- `block_pending_human_security_review`.

The planner derives required tests and always keeps `automatic_merge_allowed=false`.

### Merge receipt

A receipt binds:

- branch DNA digest;
- base, head and optional result SHA;
- conflict counts;
- completed tests;
- artifacts;
- known residues;
- OAK verdict.

A receipt proves what the software recorded. It does not prove scientific truth, legal compliance, security, patentability, product value or absence of defects.

## Conflict interpretation

A Git conflict is treated as one observable form of non-commutativity between repository transformations. The current implementation does not claim to compute a universal BCH generator for arbitrary repositories; LOG/EXP remains the theoretical layer, while R0.1 implements bounded static checks.

## Commands

```bash
omega-convergence branch-dna examples/omega_convergence_branch_input.json \
  --output branch-dna.json
```

```bash
omega-convergence compare base-dna.json head-dna.json \
  --output conflicts.json
```

```bash
omega-convergence plan plan-input.json --output merge-plan.json
```

```bash
omega-convergence receipt receipt-input.json --output merge-receipt.json
```

## OAK boundaries

```text
mergeable != safe_to_merge
hash != truth
software test != empirical validation
synthetic validation != independent replication
large diff != high value
automatic analysis != automatic authority
```

Critical permission escalations produce a blocking verdict. Missing tests remain explicit residues. Binary files are never silently reconstructed from text.

## R0.2 candidates

- Git tree adapter and PR patch adapter;
- dependency and JSON Schema compatibility analysis;
- Python call-site impact graph;
- workflow action pinning and secret-surface audit;
- semantic documentation/code divergence checks;
- generated-file provenance and regeneration contracts;
- actual three-way tree simulator;
- signed evidence bundles;
- post-merge watch and automatic rollback proposal;
- calibration corpus of historical good and bad merges.
