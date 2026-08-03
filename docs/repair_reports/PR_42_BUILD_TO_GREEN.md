# PR #42 Build-To-Green repair report

PR: `#42 — Ω-TRANSFORM-T FWT/FFWT/FFWT-N prototype`

## Decision

`manual_required`

## Current state

- PR is open but still marked `draft`.
- GitHub reports `mergeable=false`.
- The PR correctly records M⁻: the current FFWT fertility heuristic is not superior on sparse reconstruction at the same keep fraction.

## Why not merge automatically

This PR contains executable transform research plus explicit negative memory. It should be reviewed to preserve the anti-overclaiming result, benchmark framing and reproducibility before promotion to `main`.

## Safe path to green

1. Keep the PR as draft until benchmark/OAK review is complete.
2. Preserve the M⁻ result: FWT beats the current FFWT heuristic for reconstruction in the recorded setup.
3. Confirm CI runs compile, unit tests, OAKBench, anomaly demo and extreme OAKBench.
4. Confirm import paths are self-contained for all scripts when invoked from repository root.
5. Re-check mergeability after syncing with `main`.
6. Merge only after `draft=false`, `mergeable=true`, and required checks are green.

## Forbidden actions

- Do not mark ready automatically.
- Do not weaken the benchmark or remove M⁻.
- Do not claim FFWT superiority without task-specific evidence.
- Do not merge while `draft=true` or `mergeable=false`.

## OAK invariant

```text
No revolution without benchmark; negative results are canon memory, not failures to hide.
```
