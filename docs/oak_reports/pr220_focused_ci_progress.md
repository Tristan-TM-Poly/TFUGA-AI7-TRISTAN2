# PR #220 Focused CI Progress

## Scope

This report records the safe transition after the import-smoke planning pass and the follow-up debug hardening pass.

## Added

- `.github/workflows/pr220-focused-tests.yml`

## Debug hardening update

The workflow has been hardened with two OAK-safe changes:

1. `actions/checkout` now uses `persist-credentials: false`.
2. A `Static compile smoke` step now runs before pytest:

```bash
python -m compileall -q tools tests
```

This catches syntax/import-surface failures earlier and reduces credential exposure during CI.

## Status

The focused CI workflow is a draft PR artifact. It is designed to run pytest groups for the PR #220 stack.

This report does not claim that the workflow has passed on the newest head. Test execution results must come from GitHub Actions or another controlled runtime.

## Current classification

`focused_ci_hardened`, not `merge_ready`.

## Intended test groups

- core safety tests
- reality and forge tests
- CanonOS tests
- ResearchFactory and ContinuationEngine tests
- PropulsionMesh and SelfStabilizingRefactorKernel tests
- PR220 import smoke test

## OAK boundaries

- No auto-merge.
- No release.
- No deployment.
- No external contact.
- No status transition claimed.
- No readiness claim until the current head has completed checks.

## M+

- Workflow uses read-only permissions.
- Checkout credentials are no longer persisted.
- Static compile smoke now precedes grouped pytest execution.

## M-

- A planned workflow is not a passed workflow.
- A draft PR remains a hard no-merge gate.
- Large hyperstructure PRs must not be marked ready solely because local artifact structure is complete.

## Next safe move

Observe focused CI results for the current head. Convert any failing group into a self-repair packet and focused patch plan before any ready-for-review or merge transition.
