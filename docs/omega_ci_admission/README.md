# Ω-CI-ADMISSION-T R0.1

## Path-aware CI admission without deleting validation

A small shared change such as `pyproject.toml` currently wakes several
independent scientific matrices. The resulting fan-out delays the checks that
actually correspond to the changed module.

R0.1 introduces an evidence-first replacement path:

```text
changed files
  -> scan legacy triggers and static matrix axes
  -> estimate legacy fan-out
  -> select owned scientific routes
  -> select shared validators
  -> execute allowlisted suites
  -> preserve receipts and admission report
  -> require a reviewed green replacement receipt
  -> only then consider legacy-trigger migration
```

## Current safety state

```json
{
  "dry_run": true,
  "safe_to_change_legacy_triggers": false,
  "workflow_mutation_performed": false,
  "workflow_cancellation_performed": false,
  "workflow_dispatch_performed": false,
  "replacement_green_receipt_present": false
}
```

This PR does not edit, disable, cancel or delete any existing workflow.

## Problem Atlas ownership

The route table covers R0.3 through R0.11. Each route owns only its module,
tests, schemas, documentation and historical workflow file.

A change to:

```text
omega_millennium_t/r11/model.py
```

selects the R0.11 suite on Python 3.10–3.13. It does not select R0.3–R0.10.

A simultaneous change to:

```text
pyproject.toml
```

selects one shared static entry-point validator rather than every historical
scientific matrix. The expected replacement fan-out is therefore five jobs:

```text
R0.11: 4 Python jobs
CLI registry: 1 job
```

## Scanner

The scanner reads GitHub workflow YAML using `yaml.BaseLoader` so that the
`on` key is not coerced to a boolean. It records:

- workflow path and name;
- trigger events;
- pull-request path filters;
- unfiltered pull-request triggers;
- static matrix expansion estimate;
- concurrency declaration;
- workflow-dispatch and workflow-call availability;
- dynamic matrix warnings.

The estimate is not presented as exact GitHub scheduler truth.

## Route configuration

`config/omega_ci_admission/problem_atlas_routes.json` contains:

- nine routes from R0.3 through R0.11;
- structured command argument arrays;
- legacy workflow coverage patterns for `.yml` and `.yaml`;
- one shared validator for `pyproject.toml`;
- a null replacement green receipt.

The configuration audit fails if a scoped legacy workflow is uncovered or
matched by multiple routes.

## Allowlisted execution

The runner accepts only a configured route or validator ID. It:

- resolves arguments from reviewed JSON;
- expands test-file globs itself;
- permits only `pytest` or `python` executables;
- rejects shell metacharacters;
- invokes `subprocess.run(..., shell=False)`;
- writes a receipt containing the exact argument vector and return code.

A pull request cannot provide an arbitrary executable or shell command.

## Shared CLI validator

The shared validator parses `pyproject.toml` and statically checks every
`[project.scripts]` target:

- module file exists;
- target attribute is defined or imported at top level;
- Python source parses;
- no module is imported or executed.

This catches broken CLI registrations without running every scientific suite.

## Replacement workflow

`.github/workflows/omega-problem-atlas-router.yml` performs:

1. router compilation and self-tests;
2. changed-file collection;
3. dry-run fan-out analysis;
4. observation-boundary assertions;
5. minimal route matrix execution;
6. shared validator execution;
7. JSON execution receipts;
8. 14-day admission-report artifacts;
9. estimated legacy versus replacement job summary.

The legacy workflows still execute in parallel during the observation phase.

## Commands

```bash
python -m omega_ci_admission_t.cli scan \
  --repository-root .

python -m omega_ci_admission_t.cli audit-config \
  --repository-root . \
  --config config/omega_ci_admission/problem_atlas_routes.json

python -m omega_ci_admission_t.cli route \
  --repository-root . \
  --config config/omega_ci_admission/problem_atlas_routes.json \
  --changed-file omega_millennium_t/r11/model.py \
  --changed-file pyproject.toml \
  --output generated/omega_ci_admission/report.json
```

`audit-config` intentionally exits non-zero while the replacement green receipt
is missing.

## Migration protocol

### Phase A — observation

- keep all historical triggers;
- run replacement routes in parallel;
- compare outcomes and selected coverage;
- preserve failed or missing routes in M−;
- measure actual queue and runtime effects;
- accumulate multiple green receipts.

### Phase B — reviewed migration

A later PR may modify one legacy workflow at a time only after:

- all scoped workflows are covered exactly once;
- replacement suites repeatedly pass;
- required branch-protection check names are mapped;
- manual `workflow_dispatch` deep validation remains available;
- rollback instructions are prepared;
- a reviewed replacement green receipt is committed.

R0.1 implements Phase A only.

## Negative memory M−

- Do not disable workflows before replacement evidence exists.
- Do not treat static matrix estimates as scheduler truth.
- Do not execute route commands through a shell.
- Do not let a shared file select every scientific suite.
- Do not ignore unfiltered workflows.
- Do not accept uncovered or ambiguous legacy coverage.
- Do not declare the saturation problem solved from one green run.
- Do not cancel unrelated workflows automatically.
- Do not change branch protection without migration evidence.

## OAK status

`CERTIFIED_CI_ADMISSION_OBSERVER_R0_1` may certify deterministic route selection,
allowlisted execution and dry-run boundaries after CI succeeds.

It does not certify exact queue reduction, scheduler behavior or permission to
remove historical validation.
