# Ω-HYDROQUÉBEC-TRISTAN-T∞ R0.2 MAX

## Public Evidence Mirror

R0.2 converts the R0.1 synthetic grid laboratory into an **offline-first public evidence mirror**. It compiles explicitly supplied local exports into versioned observations, claims, evidence links, contradictions, model-disagreement residues and security assessments.

The core pipeline is:

```text
authorized local export
→ policy and licence gate
→ normalization and units
→ prohibited-field screening
→ quarantine or accepted observation
→ immutable temporal snapshot
→ Claim–Evidence Graph
→ contradiction and model-disagreement analysis
→ composability-risk review
→ OAK receipt
```

## Delivered capabilities

- JSON, JSONL and CSV offline ingestion;
- explicit source descriptors, licences and permitted/prohibited uses;
- byte and row ceilings;
- units, timestamps, quality flags and uncertainty validation;
- deterministic deduplication;
- quarantine receipts for rejected rows;
- observation and receipt Merkle roots;
- immutable snapshots with parent identifiers and deterministic diffs;
- descriptive claims linked to observation identifiers;
- numeric contradiction objects instead of silent averaging;
- persistence-versus-linear-trend comparison;
- public-data mosaic/composability risk scoring;
- mission compiler that refuses operational or control objectives;
- JSON Schema catalog and Python 3.10–3.13 CI;
- deterministic OAK benchmark.

## Canonical invariants

1. Every accepted observation retains source, unit, timestamp, region, uncertainty, method and source-row provenance.
2. Every accepted source has explicit licence metadata.
3. Every snapshot has an observation Merkle root.
4. Every claim carries evidence identifiers, assumptions, scope and validity interval.
5. Contradictions remain visible and reviewable.
6. Model disagreement is an OAK residue, not noise to hide.
7. Public datasets may become sensitive when combined; aggregation does not eliminate mosaic risk.
8. Offline ingestion certifies traceable processing of the supplied export, not the truth or completeness of the publisher's data.

## Claim–Evidence Graph

R0.2 emits narrowly scoped descriptive claims. A claim records:

- subject, predicate and value;
- validity window;
- confidence derived from declared uncertainty;
- supporting and counter-evidence identifiers;
- assumptions;
- status and scope.

Claims sharing subject, predicate and validity interval are compared. Numeric disagreements beyond tolerance become explicit contradiction objects. Contradiction detection does not establish causality, misconduct or institutional wrongdoing.

## Temporal mirror

Snapshots are immutable projections over sorted observation identifiers and Merkle roots. A snapshot can reference a parent. A diff reports additions, removals, unchanged observations and changed series.

A removal is not interpreted automatically. It may represent a correction, scope change, retention policy, supersession or data loss.

## Security and data policy

Accepted inputs are public, public-aggregated or synthetic local exports. The default policy rejects unknown licences, unsupported source kinds, non-public sensitivity and prohibited field names.

The policy blocks or quarantines indicators of:

- SCADA tags;
- relay settings;
- credentials;
- customer accounts;
- exact substation topology;
- control commands;
- private personal identifiers.

This lexical gate is not sufficient by itself. Semantic human review remains mandatory before publication or external sharing.

## Non-goals

R0.2 performs no network crawling, authentication bypass, SCADA/EMS connection, real-grid topology reconstruction, customer profiling, operational dispatch, protection engineering or autonomous control. It does not imply affiliation, endorsement or validation by Hydro-Québec.

## Quick start

```bash
python -m omega_hqt_t.r02 benchmark --hours 24
python -m omega_hqt_t.r02 campaign --output-dir generated/omega_hqt_t/r0.2
python -m omega_hqt_t.r02 mission "compare regional public energy indicators"
omega-hqt-r02 benchmark --hours 24
```

## Benchmark claim boundary

A passing result means only that the synthetic fixtures are processed deterministically, schemas and safety gates behave as tested, evidence links exist and prohibited operational claims remain false. It does not validate the real Québec grid or authorize operational use.

## R0.3 candidates

- signed source manifests and detached content hashes;
- revision-aware public-document extracts;
- dimensional unit ontology;
- calibration and reliability diagrams;
- graph database exporters;
- independently reviewed public-source adapters;
- differential-privacy experiments for publication layers;
- source correction and supersession workflows;
- multi-model physical comparison using authorized synthetic benchmarks.
