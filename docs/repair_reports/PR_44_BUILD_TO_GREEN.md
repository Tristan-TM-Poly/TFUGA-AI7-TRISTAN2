# PR #44 Build-To-Green repair report

PR: `#44 — Ω-SCI-PATENT-QC-DIGEST-T MAX scaffold`

## Decision

`manual_required`

## Current state

- PR is open but still marked `draft`.
- GitHub reports `mergeable=false`.
- The PR overlaps conceptually with later Ω-SCI-PATENT-QC-DIGEST-T source work.

## Why not merge automatically

This is a scaffold/source-tree PR for scientific-publication and patent digestion. It has public-disclosure/IP/legal-risk boundaries and may overlap with later PRs, so semantic deduplication and OAK-IP review are required before merge.

## Safe path to green

1. Decide whether #44 remains the canonical scaffold, is superseded by #47, or should be split into a Lite public-safe subset.
2. Confirm synthetic-fixture-only behavior and no live source fetching by default.
3. Confirm outputs carry OAK warnings and do not produce legal/patent/FTO/revenue conclusions.
4. Run/inspect CI for the package and examples.
5. Re-check mergeability after syncing with `main`.
6. Merge only after `draft=false`, `mergeable=true`, and required checks are green.

## Forbidden actions

- Do not mark ready automatically.
- Do not resolve overlap by deleting theory/source content blindly.
- Do not add private data, secrets, or live scraping by default.
- Do not merge while `draft=true` or `mergeable=false`.

## OAK invariant

```text
A science-IP scaffold must preserve confidentiality, provenance, licensing, and claim-status boundaries before publication.
```
