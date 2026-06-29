# PR #47 Build-To-Green repair report

PR: `#47 — Ω-SCI-PATENT-QC-DIGEST-T source v0.4`

## Decision

`manual_required`

## Current state

- PR is open but still marked `draft`.
- GitHub reports `mergeable=false`.
- The PR body says it should remain draft until CI has run and OAK review confirms what can be public in `main`.

## Why not merge automatically

This branch handles scientific-publication and patent-opportunity digestion. Even with synthetic fixtures, accidental public disclosure, legal overclaiming, patentability/FTO confusion, or source/license misuse would be high-risk.

## Safe path to green

1. Keep the PR as draft until OAK-IP review is complete.
2. Verify the package uses synthetic fixtures only and performs no live scraping/API calls by default.
3. Confirm every output says: no legal advice, no patentability conclusion, no FTO conclusion, no revenue guarantee.
4. Confirm CI runs:

```bash
cd projects/qc_scipatent_digest
python -m pip install -e .
python -m pytest -q
python -m qc_scipatent_digest.cli plus-ultra --out outputs/plus_ultra_v04
```

5. Re-check mergeability after syncing with `main`.
6. Merge only after `draft=false`, `mergeable=true`, and required checks are green.

## Forbidden actions

- Do not mark ready automatically.
- Do not add real patent/legal conclusions.
- Do not add live API keys or scrape private/non-permitted sources.
- Do not merge while `draft=true` or `mergeable=false`.

## OAK invariant

```text
Science-IP opportunity discovery is not legal advice, patentability, FTO, or public-disclosure approval.
```
