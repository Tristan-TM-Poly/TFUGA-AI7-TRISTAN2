# PR #165 Build-To-Green / Draft Sweep report

PR: `#165 — Ω-ACTION-EXT-T MVP: OAK-safe external action kernel`

## Decision

`draft_enrichment_active_zero_manual`

## Current state

- PR is open and intentionally still marked `draft`.
- Latest known branch mode: additive external-action kernel MVP.
- GitHub mergeability can temporarily recalculate after main moves; after recalculation the PR returned to `mergeable=true`.
- The PR remains non-mergeable by policy while `draft=true`.

## Why not merge automatically

This PR touches an external-action kernel. Even though the MVP is dry-run-first, the future surface includes email, calendar, GitHub, Drive, payments, publication, permissions, reputation, IP and legal-sensitive actions.

Zero-manual does **not** mean unsafe autonomy. It means the system keeps enriching the draft by adding tests, docs, validators, proof ledgers, rollback recipes, dry-run connectors, leak scans, and M⁻ memory without sending routine work back to Tristan.

## Zero-manual enrichment already added

- `green_builder.py` — blocked PR → Build-To-Green plan.
- `pr_green_pipeline.py` — PR state → plan + ActionManifest + batch report.
- `zero_manual_forge.py` — autonomous-safe tactics for conflicts, failing checks, pending checks and clean merges.
- `draft_sweep.py` — readiness scoring for draft PRs without marking them ready automatically.
- Tests for all of the above.
- Docs for PR Build-To-Green and Zero-Manual PR Forge.

## Next autonomous actions

1. Keep PR as draft until explicit ready decision exists outside this module.
2. Continue scoring draft readiness automatically.
3. Add or repair missing tests/docs/guardrails if readiness score drops.
4. Never mark ready automatically.
5. Never merge while `draft=true`.
6. When a future explicit ready decision exists, merge only if open, non-draft, mergeable, green, conflict-free and matching expected head SHA.

## Forbidden actions

- Do not mark ready automatically.
- Do not bypass draft status.
- Do not expose secrets or add live credentials.
- Do not add real-world actuators without dry-run and explicit approval gates.
- Do not weaken tests to make CI green.
- Do not merge while `draft=true` or checks are pending/failing/ambiguous.

## OAK invariant

```text
Zero manual = autonomous enrichment + proof + green-only merge.
Zero manual ≠ bypassing draft, safety, checks, consent, or OAK gates.
```
