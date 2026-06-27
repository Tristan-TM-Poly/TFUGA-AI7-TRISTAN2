# QC-DIGEST Tristan Local Workflow

Issue: #52

## Purpose

Define a reproducible local workflow for Tristan's own corpus, research directions, invention map, and selected open metadata.

The workflow is local-first and dry-run by default.

## Command target

```bash
python -m qc_digest plus-ultra --profile tristan-live --dry-run --output outputs/tristan_live
```

This is a target contract. Implementation can evolve, but future commands should preserve the same safety properties.

## Inputs

Allowed input classes:

- generated demo data;
- Tristan-owned notes converted into reviewed local files;
- selected public metadata;
- reviewed CSV files.

## Outputs

Target folder:

```text
outputs/tristan_live/
  manifest.json
  checksums.json
  report.md
  review_queue.json
  opportunity_matrix.csv
```

Generated outputs stay local by default.

## Manifest contract

Each run should record:

- profile;
- input names;
- query summary;
- date range;
- max records;
- tool version;
- output files;
- review state.

## Checksum contract

Each shared output should have a checksum entry.

## Review states

- `draft`
- `review_required`
- `public_ok`
- `local_only`
- `blocked`

## OAK boundary

- no automatic publication;
- no external affiliation claim;
- no legal or patentability claim;
- no sensitive output release by default;
- every claim keeps source trace and uncertainty.

## Done when

- one local command target is documented;
- output contract is documented;
- manifest and checksum fields are documented;
- review states are documented;
- output policy remains local-first.
