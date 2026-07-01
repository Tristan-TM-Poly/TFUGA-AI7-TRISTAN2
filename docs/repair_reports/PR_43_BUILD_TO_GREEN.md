# PR #43 Build-To-Green repair report

PR: `#43 — ServiceGraph-QC MVP`

## Decision

`manual_required`

## Current state

- PR is open but still marked `draft`.
- GitHub reports `mergeable=false`.

## Why not merge automatically

The PR models public-service reform workflows. Even if the current code is diagnostic and stdlib-only, it touches civic/government-service concepts where privacy, accessibility, recourse, human oversight and institutional accuracy matter.

## Safe path to green

1. Keep the PR as draft until human review confirms scope and public-safe framing.
2. Confirm examples use synthetic/public-safe data only.
3. Confirm outputs are recommendations/diagnostics, not automated eligibility or service decisions.
4. Add/confirm tests for service-model parsing, OAK scoring, friction mapping, and M⁻ registry behavior.
5. Re-check mergeability after syncing with `main`.
6. Merge only after `draft=false`, `mergeable=true`, and required checks are green.

## Forbidden actions

- Do not mark ready automatically.
- Do not add personal citizen data.
- Do not create automated government-service decisions.
- Do not merge while `draft=true` or `mergeable=false`.

## OAK invariant

```text
Public-service intelligence must preserve human recourse, privacy, accessibility, and auditability.
```
