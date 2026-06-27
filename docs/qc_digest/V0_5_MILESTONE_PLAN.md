# QC-DIGEST v0.5 Milestone Plan

Issue: #59  
Milestone: v0.5 Tristan-Owned Pilot + Product Surfaces

## Goal

Move QC-DIGEST from a source-kernel scaffold toward a local pilot workflow that can produce a reviewed offline report from Tristan-owned public metadata, Tristan-owned research directions, or explicitly selected open metadata without committing generated outputs by default.

This milestone does not imply affiliation with Polytechnique or any external institution. The pilot is 100% Tristan-owned unless a source is explicitly marked otherwise.

## Target command

```bash
python -m qc_digest plus-ultra --profile tristan-live --dry-run --output outputs/tristan_live
```

The exact command may change as the CLI stabilizes, but v0.5 should preserve these properties:

- dry-run or local-only mode by default;
- Tristan-owned scope by default;
- public metadata only unless explicitly configured;
- source manifest generation;
- checksums for generated outputs;
- review state attached to outputs;
- no generated live outputs committed by default.

## Scope

### 1. Tristan-owned local pilot

Minimum local pilot around Tristan's own corpus, research directions, invention map, and selected public metadata sources.

Deliverables:

- bounded query profile;
- date and record limits;
- source manifest;
- reviewed offline report;
- M-minus notes for ambiguity and false positives;
- explicit ownership/scope label for every output.

Related issue: #52 should be retargeted from an institution-specific pilot to a Tristan-owned pilot before implementation.

### 2. Adapter interfaces

Reusable adapter boundary for source ingestion and future domains.

Deliverables:

- adapter protocol;
- fixture adapter;
- optional public metadata adapter;
- local CSV import path.

Related issues: #49 and #54.

### 3. Source manifests and checksums

Every run should be reproducible and auditable.

Deliverables:

- manifest writer;
- checksum registry;
- run metadata;
- review state;
- ownership/scope field.

Related issue: #64.

### 4. Product surfaces

Turn digest outputs into local artifacts that can feed Tristan-owned reports, dashboards, and later services.

Deliverables:

- Markdown report;
- CSV matrix;
- SQLite or JSON export;
- dashboard-ready data folder;
- clear public/private output boundary.

Related issues: #50 and #62.

### 5. GitHub issue export preview

Generate local issue drafts without posting by default.

Deliverables:

- JSON issue draft;
- Markdown issue draft;
- OAK status;
- source references;
- uncertainty and M-minus notes;
- explicit label that drafts are Tristan-owned work items, not institutional claims.

Related issue: #53.

## Done when

A user can run one local command and receive:

- source manifest;
- reviewed offline report;
- checksums;
- local output folder;
- clear review state;
- explicit Tristan-owned scope label;
- no live output committed by default.

## OAK boundary

- No legal advice.
- No patentability claim.
- No affiliation claim without source support.
- No implied affiliation with Polytechnique or any external institution.
- No live output release without review state.
- No private notes in public commits.
- Every generated claim keeps uncertainty and source trace.

## Execution order

1. #60 deterministic demo data generator.
2. #64 provenance manifests and checksum registry.
3. #54 plugin adapter architecture.
4. #49 public metadata adapters behind dry-run mode.
5. #50 productized local output surfaces.
6. #53 local issue export preview.
7. #52 Tristan-owned local dry-run pilot.

## M-minus

- Public metadata can be stale or ambiguous.
- Institution and author matching can create false positives.
- Opportunity scoring is heuristic until validated.
- Live outputs should remain local unless reviewed.
- Generated reports are not evidence of commercial value by themselves.
- The default ownership/scope is Tristan-owned; external institution framing must be opt-in and source-backed.
