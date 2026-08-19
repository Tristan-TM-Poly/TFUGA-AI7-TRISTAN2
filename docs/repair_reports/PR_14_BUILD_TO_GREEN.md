# PR #14 Build-To-Green repair report

PR: `#14 — interrepo HGFM atlas max`

## Decision

`manual_required`

## Current state

- PR is open but still marked `draft`.
- GitHub reports `mergeable=false`.
- The branch is a docs/YAML atlas packet.

## Why not merge automatically

The PR maps several repositories and canon layers. Since the repository has moved forward, the atlas may now be stale or need synchronization with newer merged branches.

## Safe path to green

1. Keep the PR as draft until atlas freshness is reviewed.
2. Compare repository names, roles and branch states against current reality.
3. Preserve the atlas as historical/canon context if stale, or update it through a new reviewed commit.
4. Re-check mergeability after syncing with `main`.
5. Merge only after `draft=false`, `mergeable=true`, and required checks are green or not required for docs/YAML scope.

## Forbidden actions

- Do not mark ready automatically.
- Do not publish stale repository-state claims as current without review.
- Do not overwrite newer atlas/canon materials.
- Do not merge while `draft=true` or `mergeable=false`.

## OAK invariant

```text
An atlas must distinguish current map, historical snapshot and speculative route.
```
