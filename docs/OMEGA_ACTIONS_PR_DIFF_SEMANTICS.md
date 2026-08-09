# Ω-ACTIONS-T∞ — PR-Diff Semantics & Problem Atlas Trigger-Cut Protocol

## Why this gate exists

GitHub Actions `pull_request.paths` selection must be reasoned about from the cumulative pull-request diff (`base..head`), not only from the latest commit. A workflow file changed earlier in the same PR can therefore remain eligible through its self-path even when a later witness commit touches only an unrelated file.

Ω-ACTIONS now treats this as an experimental-validity problem rather than a CI implementation detail.

## Corrected Code Dojo interpretation

PR #367 migrated the five Code Dojo workflows away from the shared `pyproject.toml` trigger. A later witness head (`e1fa9624f0a521933755c3036ee4c9101635c0fd`) changed only `pyproject.toml` in its latest commit, but the five Code Dojo workflow YAML files are themselves part of the cumulative PR diff.

Result: Code Dojo remains eligible on the PR. This is **not evidence that the trigger cut failed**, and it is **not evidence that it succeeded**. The same-PR witness is classified:

`PR_DIFF_CARRYOVER_CONTAMINATED`

The valid after-test is a fresh post-merge PR (or another isolated branch whose cumulative diff does not contain the migrated workflow files).

## Clean pre-migration baseline: Problem Atlas

At head `e1fa9624f0a521933755c3036ee4c9101635c0fd`, the latest commit changes `pyproject.toml`, while none of the nine specialized Problem Atlas workflow YAML files below are part of PR #367's changed-file set. GitHub nevertheless instantiated their PR workflow runs.

Manual dependency inspection found the same architecture in all nine specialized lanes: their jobs invoke repository modules/tests directly and install only test/validation dependencies; they do not install the project from `pyproject.toml` and do not directly consume that file in the job body.

Candidate trigger cuts:

- `.github/workflows/omega-problem-atlas-r03.yml`
- `.github/workflows/omega-problem-atlas-r04-sources.yml`
- `.github/workflows/omega-problem-atlas-r05-identity.yml`
- `.github/workflows/omega-problem-atlas-r06-evidence.yml`
- `.github/workflows/omega-problem-atlas-r07-runners.yml`
- `.github/workflows/omega-problem-atlas-r08-routing.yml`
- `.github/workflows/omega-problem-atlas-r09-promotion.yml`
- `.github/workflows/omega-problem-atlas-r10-streaming.yml`
- `.github/workflows/omega-problem-atlas-r11-competition.yml`

Their static matrix topology represents **37 specialized jobs of potential eligibility** for a `pyproject.toml`-only PR: eight four-version Python matrices plus R0.10's four-version core and one finite-scale successor job. This is a structural upper-bound signal, not billed-compute evidence.

## Intentional exception: Admission Router

`.github/workflows/omega-problem-atlas-router.yml` must remain sensitive to `pyproject.toml`.

Unlike the specialized OAKBench lanes, the router explicitly compiles/tests `tools/ci/validate_pyproject_entrypoints.py`, installs TOML parsing support, computes the cumulative PR changed-file set, and produces an admission plan. The desired topology is therefore:

`pyproject.toml -> one shared admission/project-surface validation path -> only impacted specialized suites`

not:

`pyproject.toml -> every specialized Problem Atlas OAKBench`

## PR-Diff Semantics Gate

`omega_actions_t.pr_diff_gate` compares two path sets:

- `commit_changed_paths`: latest commit only;
- `pull_request_changed_paths`: cumulative PR `base..head` diff.

Per workflow it emits one of:

- `ATTRIBUTABLE_TO_LATEST_COMMIT`
- `PR_DIFF_CARRYOVER_CONTAMINATED`
- `MIXED_PR_DIFF_CONTAMINATION`
- `NOT_ELIGIBLE_UNDER_PR_DIFF`
- `BROAD_OR_NEGATIVE_FILTER_ONLY`
- `OUT_OF_SCOPE_EVENT`
- `INCONSISTENT_DIFF_INPUT`

A contaminated status makes `measurement_valid=false`. This prevents Ω-ACTIONS Promotion Gate logic from treating a same-PR topology experiment as causal proof.

## Trigger Dependency Audit

`omega_actions_t.trigger_dependency` separates trigger frequency from observed job dependency. For a requested trigger path it classifies each workflow as:

- `DIRECT_RUNTIME_REFERENCE`
- `PROJECT_INSTALL_SIGNAL`
- `NO_DIRECT_RUNTIME_SIGNAL`

`NO_DIRECT_RUNTIME_SIGNAL` means *migration candidate only*. It cannot prove the absence of transitive packaging, metadata, policy, required-check, generated-code or repository-level dependencies.

## OAK migration protocol

1. Capture an uncontaminated pre-migration baseline while target workflow YAMLs are untouched.
2. Audit direct/runtime dependency on the shared trigger path.
3. Preserve every validation command, matrix member, permission boundary and self-workflow trigger.
4. Remove only the unjustified global trigger edge.
5. Keep one shared validator/router when the global file truly has shared semantics.
6. Merge only after required-check and branch-protection review.
7. Run the after-test on a fresh PR whose cumulative diff excludes the migrated workflow files.
8. Compare workflow eligibility first; then queue time, wall time and compute only when completed telemetry exists.
9. Record regressions and false causal inferences in M-minus.

## OAK claim boundary

Current state: **pre-migration attribution captured; after-migration causal proof pending**.

No percentage speedup, billed-minute saving or wall-time reduction is certified from the current queued run set. The valid current claim is narrower: `pyproject.toml` is a demonstrated shared eligibility edge for the untouched Problem Atlas family, and nine specialized lanes show no direct runtime dependency signal under manual inspection. The automated Dependency Audit is designed to reproduce that candidate screening conservatively.
