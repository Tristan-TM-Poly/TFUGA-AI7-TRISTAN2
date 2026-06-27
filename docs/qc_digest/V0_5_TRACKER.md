# QC-DIGEST v0.5 Tracker

Issue: #59

## Milestone objective

Produce a reviewed offline report from public metadata with local outputs, manifests, checksums, and review state.

## Work queue

| Order | Issue | Workstream | Output | Gate |
|---:|---:|---|---|---|
| 1 | #60 | demo data | deterministic fixture generator | generated sample only |
| 2 | #64 | provenance | manifest + checksum registry | reproducible run |
| 3 | #54 | architecture | adapter/exporter protocols | pluggable core |
| 4 | #49 | adapters | public metadata adapters | dry-run default |
| 5 | #50 | product surfaces | markdown/csv/json/sqlite/dashboard data | local output default |
| 6 | #53 | issue drafts | local issue preview | no posting by default |
| 7 | #52 | live pilot | Polytechnique dry-run profile | review state required |

## Release gates

- `G0`: tests or validation path exists.
- `G1`: source manifest exists when data is used.
- `G2`: checksums exist for shared outputs.
- `G3`: output policy is followed.
- `G4`: review state is explicit.
- `G5`: M-minus is included.

## Command target

```bash
python -m qc_digest plus-ultra --profile poly-live --dry-run --output outputs/poly_live
```

## Output contract

```text
outputs/poly_live/
  manifest.json
  checksums.json
  report.md
  review_queue.json
  opportunity_matrix.csv
```

Generated outputs stay local by default.
