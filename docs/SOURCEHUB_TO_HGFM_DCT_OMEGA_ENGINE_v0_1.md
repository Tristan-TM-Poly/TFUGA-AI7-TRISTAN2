# TFUGA SourceHub-to-HGFM DCT-Omega Engine v0.1

Status: X - crystallizable
Branch: docs/sourcehub-to-hgfm-dct-omega-v0-1
Date: 2026-05-06

## Purpose

This document defines the first operational crystal for a SourceHub-to-HGFM engine: a pipeline that ingests GitHub and Google Drive sources, extracts traceable objects, classifies claims, builds DCT-Omega cards, computes PowerScore, and emits a sparse HGFM map for canonization.

The goal is not to claim that all sources have already been standardized. The goal is to define a reproducible engine that makes future standardization auditable.

## Core principle

Generate much, test locally, canonize little, reuse everywhere.

## Inputs

- GitHub repositories, files, commits, issues, pull requests;
- Google Drive documents, sheets, slides, exports, folders;
- local uploaded files or ZIP archives;
- notebooks and code artifacts;
- reports, publications, manifests, and archives.

## Outputs

- `source_index.csv`: source inventory;
- `claim_ledger.csv`: extracted claims and evidence status;
- `dct_cards/`: one DCT-Omega card per high-value object;
- `powerscore.csv`: scored objects;
- `hgfm_graph.json`: nodes and hyperedges;
- `audit_report.md`: human-readable status report;
- `promotion_log.md`: S0-S6 / S-E-X-D-C-A transitions.

## DCT-Omega tuple

```text
DCT_Omega(x) = (D, C, T, P, V, R, L, S, N, Links)
```

Where:

- D = Document;
- C = Code or Calculation;
- T = Test;
- P = Proof or validation;
- V = Version;
- R = Risk;
- L = Limits;
- S = Status;
- N = Next action;
- Links = GitHub, Drive, reports, datasets, papers, notebooks.

## EvidenceGate S0-S6

- S0: spark or raw idea;
- S1: speculative claim;
- S2: crystallizable object with definition and test path;
- S3: locally tested or proven in a constrained setting;
- S4: tested on real data or realistic environment;
- S5: reproduced, robust, or independently checked;
- S6: canonical, stable, reusable, low-duplication.

Compatibility with readable labels:

- S/E/X/D/C/A = speculative, exploratory, crystallizable, demonstrated, canonical, archived.
- S0-S6 = finer evidence gate.

## PowerScore

```text
Power(Y) = (Fertility * Verifiability * Reusability * Impact * CanonicalCompression * Stability)
           / (Complexity * Noise * UntestedSpeculation * Risk * Duplication)
```

Rules:

- If Verifiability < 2, do not promote beyond exploratory.
- If UntestedSpeculation > 4, do not promote to canonical.
- If Risk is high and limits are absent, keep the object below demonstrated status.
- If Duplication is high, merge or archive instead of promoting.

## HGFM graph schema

Nodes:

```json
{
  "id": "string",
  "label": "string",
  "source": "github|drive|upload|manual",
  "type": "claim|document|code|test|dataset|prototype|theorem|risk|invariant",
  "status": "S0|S1|S2|S3|S4|S5|S6",
  "human_status": "S|E|X|D|C|A",
  "powerscore": 0.0,
  "links": []
}
```

Hyperedges:

```json
{
  "id": "string",
  "label": "string",
  "nodes": ["node_id"],
  "relation": "supports|depends_on|contradicts|duplicates|generalizes|tests|implements|limits",
  "evidence": "S0|S1|S2|S3|S4|S5|S6"
}
```

## Minimal engine loop

1. Inventory sources.
2. Extract objects and claims.
3. Normalize names and detect duplicates.
4. Assign initial EvidenceGate status.
5. Build DCT-Omega cards for high-value objects.
6. Compute PowerScore.
7. Build sparse HGFM graph.
8. Generate audit report.
9. Propose promotions, merges, archives, or next tests.
10. Log every decision.

## Anti-fiction execution policy

A claim of execution requires at least one trace:

- commit;
- file diff;
- generated artifact;
- test log;
- CI run;
- notebook output;
- report;
- reproducible command;
- timestamped audit note.

Symbolic protocol language is allowed, but it remains symbolic until such a trace exists.

## Minimal test for v0.1

Input:

- 5 GitHub repositories;
- 10 Google Drive files;
- 20 extracted claims.

Expected output:

- at least 5 DCT-Omega cards;
- one `claim_ledger.csv` with statuses;
- one `hgfm_graph.json` with at least 20 nodes and 10 hyperedges;
- one audit report listing: demonstrated, crystallizable, speculative, archived;
- zero canonical promotion without S5 or S6-level evidence.

## Next implementation tasks

1. Add `schemas/dct_omega.schema.json`.
2. Add `schemas/hgfm_graph.schema.json`.
3. Add `docs/CLAIM_LEDGER_TEMPLATE.csv`.
4. Add `docs/ENGINE_TEST_PLAN.md`.
5. Implement a minimal local Python prototype under `src/` in a future branch.
