# PR #220 Focused CI Progress

## Scope

This report records the safe transition after the import-smoke planning pass.

## Added

- `.github/workflows/pr220-focused-tests.yml`

## Status

The focused CI workflow is a draft PR artifact. It is designed to run pytest groups for the PR #220 stack.

This report does not claim that the workflow has passed. Test execution results must come from GitHub Actions or another controlled runtime.

## Current classification

`focused_ci_planned`, not `merge_ready`.

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

## Next safe move

Observe CI results when available, then convert any failing group into a self-repair packet and focused patch plan.
