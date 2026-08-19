# PR #149 Build-To-Green repair report

PR: `#149 — Ω-ZETA-MANDEL-T canon and prototype seed`

## Decision

`manual_required`

## Current state

- PR is open but still marked `draft`.
- GitHub reports `mergeable=false`.
- No workflow runs were observed for the inspected head SHA.

## Why not merge automatically

The PR contains math/fractal/zeta/sedenion exploratory material and explicitly warns that numerical images or patterns are not proofs of the Riemann hypothesis. This is correct OAK hygiene, but the PR is still draft and lacks observed CI validation.

## Safe path to green

1. Keep the PR as draft until the author intentionally marks it ready.
2. Add a GitHub Actions workflow or reuse an existing test workflow for the prototype smoke tests.
3. Ensure tests run with dependency-free Python or declare dependencies explicitly.
4. Keep all high-level mathematical claims classified as visualization/prototype/hypothesis, not proof.
5. Re-check mergeability against `main` after CI exists and runs.
6. Merge only after `draft=false`, `mergeable=true`, and required checks are green.

## Forbidden actions

- Do not mark ready automatically.
- Do not claim RH proof or theorem status from numerical output.
- Do not weaken OAK guardrails.
- Do not merge while `draft=true`, `mergeable=false`, or CI is absent.

## OAK invariant

```text
Fractal/numerical structure is evidence for exploration, not proof.
```
