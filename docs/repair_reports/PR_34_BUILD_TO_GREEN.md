# PR #34 Build-To-Green repair report

PR: `#34 — repo canon role`

## Decision

`manual_required`

## Current state

- PR is open but still marked `draft`.
- GitHub reports `mergeable=false`.
- The PR body is minimal, so reviewers need a clearer acceptance checklist before merge.

## Why not merge automatically

The branch appears to add repo-canon role artifacts and review scoring. Because the description is sparse and the PR is draft, automatic merge would not preserve enough reviewer context.

## Safe path to green

1. Keep the PR as draft until the author confirms whether this canon-role layer is still needed after newer canon PRs.
2. Expand the PR body or docs with the purpose, files, validation and supersession status.
3. Confirm it does not duplicate or conflict with newer merged Daily Ω/canon governance files.
4. Re-check mergeability after syncing with `main`.
5. Merge only after `draft=false`, `mergeable=true`, and required checks are green.

## Forbidden actions

- Do not mark ready automatically.
- Do not merge a sparse canon-governance PR without reviewer context.
- Do not overwrite newer canon files.
- Do not merge while `draft=true` or `mergeable=false`.

## OAK invariant

```text
Canon governance must be explicit, non-duplicative and reviewable before promotion.
```
