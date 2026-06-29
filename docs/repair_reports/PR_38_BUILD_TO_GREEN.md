# PR #38 Build-To-Green repair report

PR: `#38 — Omega-PSPT solid phases canon`

## Decision

`manual_required`

## Current state

- PR is open but still marked `draft`.
- GitHub reports `mergeable=false`.

## Why not merge automatically

This branch contains solid-state/phase-matter canon and prototypes. It correctly frames `Omega-TFTS` as a candidate, not a proven phase. Scientific-claim review is needed before merge.

## Safe path to green

1. Keep the PR as draft until OAK-Science review confirms claim statuses.
2. Confirm every material/phase claim is labeled as established physics, prototype, candidate, hypothesis, or measured result.
3. Confirm examples and tests run:

```bash
python -m pytest
python examples/omega_pspt_minimal_demo.py
```

4. Ensure no phase/material claim is promoted without benchmark, controls or measurements.
5. Re-check mergeability after syncing with `main`.
6. Merge only after `draft=false`, `mergeable=true`, and required checks are green.

## Forbidden actions

- Do not mark ready automatically.
- Do not claim discovery of a physical phase without evidence.
- Do not delete OAK caveats or falsification criteria.
- Do not merge while `draft=true` or `mergeable=false`.

## OAK invariant

```text
Candidate phase != measured phase; prototype descriptor != physical discovery.
```
