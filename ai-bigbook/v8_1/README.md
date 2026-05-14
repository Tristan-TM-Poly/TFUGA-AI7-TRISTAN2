# AI-BIGBOOK V8.1 / V8.3 Canon Import

This folder replaces the old ZIP-based workflow with a GitHub-native structure.

## Core law

```text
Dream in R0.
Model in R2.
Prototype in R3.
Measure in R4.
Claim R5 only when reproducible.
```

## What belongs here

- `docs/`: V8 and V8.1 analysis, canon spec, safety gates, implementation plan.
- `data/`: canonical JSON/CSV/YAML inputs and integrity metadata.
- `src/`: Python, C++, Rust, and AMD64 source kernels.
- `reports/`: execution and verification reports.
- `dashboards/`: local HGFM HTML dashboard.
- `scripts/`: materialization helpers so large generated artifacts can be rebuilt locally.
- `specs/`: V8.3 meta-synergy additions, EvidenceGate rules, agent contracts, and claims registry seed.

## Generated artifacts policy

The old ZIP included binary SQLite artifacts. In this GitHub import, SQLite is treated as a generated artifact rather than source-of-truth.

Source-of-truth data should be kept as JSONL/CSV/YAML plus rebuild scripts. This keeps GitHub clean and avoids hauling ZIP files around.

## Canon equation

```text
Corpus -> FFWT -> objects -> block tensors -> HGFMnD2 -> HMAGFM2 -> EvidenceGate -> local patch
```

## Safety stance

This repository is `local_patch_only` by default:

- no autonomous cloud deploys,
- no payments,
- no self-replication,
- no external mutation without local approval,
- every strong claim requires an R0-R5 status and EvidenceGate review.
