# Ω-ACTIONS-T∞ — Trigger Cut Vertices and first fan-out migration

## Empirical finding

PR #367 changed `pyproject.toml` only to register Ω-ACTIONS CLI surfaces. Five independent Code Dojo workflows nevertheless appeared in the PR fan-out:

- R0.1 OAKBench;
- R0.2 OAKBench;
- R0.3 Learning Intelligence;
- R0.4 Problem Resolution;
- R0.5 Multi-Judge.

Inspection showed that all five already had domain-specific `paths` filters, but all five also listed `pyproject.toml`. Each workflow expands a four-version Python matrix, so a pyproject-only change could expose up to 5 × 4 = 20 Code Dojo jobs even when no Code Dojo source, test, schema, example or documentation changed.

This motivates a new Ω-ACTIONS object: a **trigger cut vertex**.

A trigger path `p` has fan-out

\[
F(p)=|\{W_i : p \in paths(W_i)\}|.
\]

High `F(p)` is not automatically wrong. Shared lockfiles, compilers or schemas can legitimately affect many workflows. But high-frequency trigger paths deserve dependency review because they can dominate queue pressure.

## First migration

For Code Dojo R0.1–R0.5:

1. remove `pyproject.toml` from the heavy domain OAKBench trigger lists;
2. preserve every existing Code Dojo compile/test/benchmark/schema assertion;
3. preserve all four Python versions for genuine Code Dojo changes;
4. add PR-scoped `concurrency` with `cancel-in-progress` only for pull requests;
5. pin checkout/setup-python/upload-artifact actions used by the migrated workflows;
6. validate the Code Dojo `[project.scripts]` surface in one lightweight central workflow whenever `pyproject.toml` changes.

The central validator is structural. It verifies that selected script targets are syntactically valid and point to repository modules that exist. It does not claim runtime equivalence and does not replace the domain OAKBench when domain files change.

## TriggerHotspots

`python -m omega_actions_t hotspots --root . --top 20`

scans positive trigger-level `paths:` entries and ranks shared trigger paths by workflow count. The purpose is to identify candidate cut vertices such as `pyproject.toml`, lockfiles, shared schemas or broad directory globs.

Frequency is evidence of possible fan-out amplification, not authorization to remove a dependency.

## OAK gate

The GitHub integration could not read branch-protection settings for `main` (`403 Resource not accessible by integration`). Therefore this migration deliberately does not delete checks or validation steps and does not modify branch protection. The Code Dojo workflows were already conditional on path filters before this change; the migration narrows one shared trigger while providing a replacement lightweight project-surface check for the removed responsibility.

## Expected effect

For a future PR that changes `pyproject.toml` but no Code Dojo domain file:

- before: up to five Code Dojo workflow runs / twenty matrix jobs can become eligible;
- after: the five heavy Code Dojo workflows are not selected by `pyproject.toml`; one project-surface job validates the Code Dojo entrypoint mappings.

This is a predicted topology change until confirmed on an independent post-migration head. Ω-ACTIONS must record the actual run set before calling the reduction measured.
