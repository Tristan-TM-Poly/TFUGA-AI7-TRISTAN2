# Ω-ACTIONS-T∞ — Problem Atlas `pyproject.toml` Trigger Cut

## Status

**Migration applied in draft PR #367; causal after-proof intentionally pending.**

The nine specialized Problem Atlas workflows R0.3/R0.4 through R0.11 previously included `pyproject.toml` in both `push.paths` and `pull_request.paths`. Their job bodies were inspected before the cut: they execute their own modules, fixtures and tests directly and install validator/test dependencies, but do not install the repository project from `pyproject.toml` or directly consume that file.

The migration removes only that shared trigger edge. It does not remove tests, matrices, OAK assertions, timeouts, permissions, workflow self-paths or manual dispatch.

## Specialized lanes cut

- `.github/workflows/omega-problem-atlas-r03.yml`
- `.github/workflows/omega-problem-atlas-r04-sources.yml`
- `.github/workflows/omega-problem-atlas-r05-identity.yml`
- `.github/workflows/omega-problem-atlas-r06-evidence.yml`
- `.github/workflows/omega-problem-atlas-r07-runners.yml`
- `.github/workflows/omega-problem-atlas-r08-routing.yml`
- `.github/workflows/omega-problem-atlas-r09-promotion.yml`
- `.github/workflows/omega-problem-atlas-r10-streaming.yml`
- `.github/workflows/omega-problem-atlas-r11-competition.yml`

Each specialized lane retains its own workflow path in its trigger set so workflow-definition changes still self-validate.

## Shared guards intentionally retained

`.github/workflows/omega-problem-atlas-router.yml` remains sensitive to `pyproject.toml` because it explicitly runs the shared project-entrypoint validator and admission logic.

`.github/workflows/omega-project-surface-ci.yml` remains a second lightweight shared guard for selected `[project.scripts]` surfaces. During this migration it was extended to validate the newly merged Ω-LATEX `omega-doc` and `omega-latex` entrypoints as well as Code Dojo.

Desired topology:

`pyproject.toml -> shared entrypoint/admission validation -> impacted domain suites`

instead of:

`pyproject.toml -> every specialized Problem Atlas OAKBench`

## Structural baseline

Clean pre-migration baseline head:

`e1fa9624f0a521933755c3036ee4c9101635c0fd`

The latest commit at that head changed only `pyproject.toml`, while the nine specialized Problem Atlas YAML files were still untouched by PR #367. GitHub instantiated the Problem Atlas family. The existing matrix topology represents an upper bound of **37 specialized job eligibilities** for the family.

That number is a structural eligibility count. It is not a claim of 37 billed jobs, a percentage speedup, saved compute minutes or wall-clock reduction.

## Why PR #367 cannot be the causal after-test

Once the nine YAML files are changed by this migration, they enter the cumulative PR diff. Because each specialized workflow deliberately includes its own YAML path, a later commit on the same PR can still make those workflows eligible through workflow self-change carry-over.

Therefore any same-PR after observation is classified by `omega_actions_t.pr_diff_gate` as contaminated when applicable. It must not be promoted as causal proof of the trigger cut.

Valid causal after-test:

1. merge only after required-check and branch-protection review and explicit authorization;
2. open or use a fresh uncontaminated PR whose cumulative diff changes `pyproject.toml` but does not contain the migrated workflow YAMLs;
3. compare workflow eligibility first;
4. compare queue p95, duration p95, failure rate and compute only from completed empirical telemetry.

## Regression gate

`tests/test_omega_actions_problem_atlas_cut.py` enforces the topology:

- all nine specialized workflows must exclude `pyproject.toml` from both `push.paths` and `pull_request.paths`;
- all nine must retain their own workflow path;
- the central Problem Atlas router must retain `pyproject.toml`;
- the machine-readable migration contract must stay aligned with the implementation;
- automatic merge remains unauthorized.

The Ω Actions Optimizer workflow now watches the specialized Problem Atlas workflow family and `config/omega_actions/**`, so a future trigger-topology change reruns this regression.

## Cross-PR integration repair

While rebasing the reasoning against current `main`, Ω-ACTIONS detected that the merged Ω-LATEX entrypoint

`omega-doc = "omega_latex_t.omega_doc_cli:main"`

referenced a repository module that was absent from the merged Ω-LATEX file set. PR #367 adds a minimal compatibility adapter `omega_latex_t/omega_doc_cli.py` that delegates to the canonical `omega_latex_t.cli.main`; no second document CLI implementation is introduced.

This is deliberately guarded by `Ω Project Script Surface`, which validates both `omega-doc` and `omega-latex` structurally without installing or importing the project.

## OAK boundary

Current certified claim: **the trigger topology has been migrated in the draft branch and protected by structural regression tests.**

Not yet certified: causal reduction in GitHub workflow eligibility, queue latency, wall time, billed compute, or failure rate after merge. Those require the fresh uncontaminated witness described above.

`automatic_merge_authorized = false`
