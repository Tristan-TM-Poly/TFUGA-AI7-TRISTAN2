# Ω-PROBLEM-ATLAS-T∞ R0.4 — Source Adapter Layer

R0.4 converts revision-pinned, offline snapshots of mathematical problem catalogs into the R0.3 JSONL import contract.

It does not crawl external sites during CI and does not certify that a catalog entry is currently open. Retrieval, parsing, status verification, mathematical evidence and theorem proof remain distinct operations.

## Pipeline

```text
source snapshot
  -> schema validation
  -> source policy gate
  -> record normalization
  -> dated status receipt
  -> accepted import OR quarantine
  -> SHA-256 manifest
  -> strict audit
```

## Commands

```bash
omega-problem-sources compile \
  --snapshot data/omega_problem_atlas_r04/clay_snapshot.sample.json \
  --snapshot data/omega_problem_atlas_r04/formal_conjectures_snapshot.sample.json \
  --output-dir generated/omega_problem_sources_r04

omega-problem-sources audit generated/omega_problem_sources_r04
```

The accepted import file can feed the MAX atlas:

```bash
omega-problem-atlas build-max \
  --output-dir generated/omega_problem_atlas_r04_max \
  --import-jsonl generated/omega_problem_sources_r04/imports.jsonl
```

## Snapshot contract

A snapshot records:

- source identifier and HTTPS locator;
- retrieval timestamp with timezone;
- source revision where required;
- retrieval mode;
- license and reuse note;
- source records.

Each record may contain:

- stable problem ID;
- title and mathematical front;
- observed status;
- exact source locator;
- concise statement or statement fingerprint;
- verification basis;
- dated status receipt;
- explicit claim flags.

## Fail-closed rules

A current-open-status claim is accepted only when:

1. `observed_status` is `open`;
2. `status_verified_at` is present and timezone-aware;
3. the source policy permits current-status claims;
4. the verification basis is accepted for that source;
5. the snapshot is not merely an offline fixture.

A violation does not produce a weakened silent import. It produces a quarantine record with reason codes and preserves the raw-record digest.

Solution claims are forbidden at this ingestion layer.

## Outputs

```text
source_snapshots.jsonl
imports.jsonl
status_receipts.jsonl
quarantine.jsonl
manifest.json
report.json
```

The manifest stores SHA-256, byte size and row count for every JSONL artifact. The strict audit recomputes receipts, counts and referential links.

## OAK interpretation

`CERTIFIED_OFFLINE_SOURCE_ADAPTER_FIXTURE_R0_4` means only that the supplied files passed the software contract. It does not mean:

- the external source was fetched by this run;
- the external page is unchanged;
- the mathematical status is current;
- the statement is complete;
- a theorem or solution was verified;
- redistribution rights were established.

Before activating a real current-status claim, create a new snapshot from an authorized retrieval or manual review, attach the exact source revision/location and date the verification receipt.
