# Global PR Forge scan — 2026-06-29

Scope: accessible Tristan GitHub repositories discovered through the GitHub connector.

## Repositories discovered

- `Tristan-TM-Poly/PEFA-FractalEnergySystem`
- `Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG`
- `Tristan-TM-Poly/Tristan_Tardif-Morency_TFUGAG`
- `Tristan-TM-Poly/TFACC`
- `Tristan-TM-Poly/TFUGA-AI7-TRISTAN2`
- `Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2`

## Active non-draft PRs observed outside TFUGA-AI7-TRISTAN2

Repository: `Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG`

- PR `#27` — `Add no-network CI for JWST AI-7 analysis lab`
- PR `#59` — `Add reusable OAK OS branch-card, report, CLI, and CI system`
- PR `#87` — `Add Ω-PR-OAK-GATE and M⁻ direct-main rule`

All three were open, non-draft and GitHub-mergeable at scan time.

## Shared blocker pattern

All three PRs had a classic status failure for:

```text
Vercel – tristan-tardif-morency-tfug-s881
```

while another Vercel context was green:

```text
Vercel – tristan-tardif-morency-tfug
```

## Actions applied

### PR #27

Zero-manual repair applied:

- replaced dependency-contradicting `pytest` invocation with stdlib direct execution;
- added a direct `__main__` runner to `jwst_ai7_analysis_lab/tests/test_core.py`;
- updated PR body to document the real dependency-free command.

Latest observed result: GitHub Actions for `JWST AI-7 no-network tests` became green on head `0ccf076...`.

Remaining blocker: external Vercel `s881` status still needs repair or OAK classification.

### PR #59

Zero-manual instrumentation applied:

- `OAK CI` now captures pytest output into `.ci-artifacts/oak-pytest.log` and uploads `oak-ci-diagnostics` on every run.
- `TFUGA Applied CI` now captures pytest output into `.ci-artifacts/pytest.log` and uploads `applied-ci-diagnostics` on every run.

This does not weaken CI. The same failing test exit code is still returned. The purpose is to make the next autonomous patch exact instead of being blocked by truncated connector logs.

### PR #87

Zero-manual instrumentation applied:

- `TFUGA Applied CI` now captures curated top-level test output into `.ci-artifacts/curated-tests.log` and uploads `applied-ci-diagnostics` on every run.

This keeps the failing exit code intact and adds machine-readable diagnostics.

## M⁻ memory

Failure class: `shared_external_status_failure`

Concrete blocker: one Vercel deployment context is red across multiple otherwise mergeable PRs.

Unsafe shortcut: merging while an external deployment status is red, or ignoring the failing context as noise without evidence.

Autonomous next action:

1. Treat this as a systemic external-status blocker.
2. Do not merge affected PRs until the red Vercel context is green or explicitly classified as non-required/noise by a repository-level OAK gate.
3. Add or update a repo-level PR gate that distinguishes required checks, optional preview checks, stale external checks, and duplicated deployment contexts.
4. If the red context is a stale or duplicate deployment, generate a machine-readable exemption proposal rather than bypassing silently.

Additional failure class: `truncated_ci_without_artifact`

Concrete blocker: failed workflow logs can be truncated by connector responses, leaving no traceback for exact repair.

Autonomous next action:

1. Preserve failing exit codes.
2. Capture command output into `.ci-artifacts/*.log`.
3. Upload diagnostics with `if: always()`.
4. Re-run workflows and patch the exact failing test from the artifact.

Anti-repetition rule:

```text
Repeated red external status across multiple PRs becomes a system blocker, not three separate manual tasks.
Truncated logs without artifacts become an instrumentation task, not a manual request.
```

## OAK decision

`zero_manual_repair_pending`

No manual work is requested from Tristan. The next forge pass should inspect uploaded diagnostics artifacts, repair exact failing tests, and separately classify or fix the duplicated/stale Vercel context.
