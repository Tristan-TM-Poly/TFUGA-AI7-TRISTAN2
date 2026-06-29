# PR #39 Build-To-Green repair report

PR: `#39 — executable Sciences de Tristan omega canon`

## Decision

`manual_required`

## Current state

- PR is open but still marked `draft`.
- GitHub reports `mergeable=false`.

## Why not merge automatically

This branch introduces a broad Sciences de Tristan canon and executable core. It spans multiple scientific domains, so claim-status and overlap review are required before promotion to `main`.

## Safe path to green

1. Keep the PR as draft until OAK-Science review confirms scope.
2. Confirm each card/claim is labeled as intuition, definition, prototype, measured result, proof/law, or speculation.
3. Run the executable core tests and CLI examples:

```bash
python -m pytest tests/test_sciences_tristan_core.py
python -m sage_tristan.sciences_tristan rank examples/sciences_tristan_seed.json
python -m sage_tristan.sciences_tristan review examples/sciences_tristan_seed.json
```

4. Confirm no physics/material/biology claim is promoted without measurements or validated baselines.
5. Re-check mergeability after syncing with `main`.
6. Merge only after `draft=false`, `mergeable=true`, and required checks are green.

## Forbidden actions

- Do not mark ready automatically.
- Do not merge broad canon while unresolved against newer merged modules.
- Do not remove uncertainty/residue/OAK language.
- Do not merge while `draft=true` or `mergeable=false`.

## OAK invariant

```text
A science operating system must keep observation, model, hypothesis, benchmark and proof separate.
```
