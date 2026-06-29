# PR #37 Build-To-Green repair report

PR: `#37 — Ω-MATH-TRISTAN canon and executable OAK kernel`

## Decision

`manual_required`

## Current state

- PR is open but still marked `draft`.
- GitHub reports `mergeable=false`.
- The branch includes both canon docs and executable scoring/kernel tests.

## Why not merge automatically

This PR changes the mathematical canon layer. It includes conjecture/prototype/proof/canon distinctions, so human review is required before promoting the theory hierarchy into `main`.

## Safe path to green

1. Keep the PR as draft until OAK-Math review confirms claim taxonomy.
2. Ensure no conjecture is promoted to theorem or canon without proof or reproducible test status.
3. Confirm tests run for scoring, OAK maturity, classification and next-action ranking.
4. Verify any README changes do not conflict semantically with newer canon layers already merged.
5. Re-check mergeability after syncing with `main`.
6. Merge only after `draft=false`, `mergeable=true`, and required checks are green.

## Forbidden actions

- Do not mark ready automatically.
- Do not erase proof/prototype/conjecture boundaries.
- Do not resolve canon conflicts by overwrite.
- Do not merge while `draft=true` or `mergeable=false`.

## OAK invariant

```text
Mathematical fertility is not proof; proof status must be explicit and preserved.
```
