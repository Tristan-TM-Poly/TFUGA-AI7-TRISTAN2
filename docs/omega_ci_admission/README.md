# Ω-CI-ADMISSION-T R0.1

## Path-aware admission without deleting validation

The repository currently contains many independent workflows. A small shared
change such as `pyproject.toml` can trigger several unrelated matrices and keep
new scientific checks queued behind work that does not inspect the changed
module.

This package introduces an evidence-first migration path:

```text
changed files
  -> scan current workflow triggers
  -> estimate legacy fan-out
  -> map owned files to minimal scientific suites
  -> map shared files to shared validators
  -> run replacement suites in parallel
  -> collect receipts
  -> compare replacement coverage with legacy coverage
  -> require an explicit green receipt
  -> only then propose legacy-trigger edits
```

## Current mode

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

No historical workflow is disabled, cancelled or rewritten in this PR.

## Why a dry-run phase is mandatory

Changing workflow triggers can create false green states when:

- a legacy suite has no replacement route;
- a matrix axis is not reproduced;
- a shared validator is missing;
- path globs differ from GitHub's exact semantics;
- a workflow performs a hidden integration or security check;
- branch protection expects a historical check name;
- the replacement has never completed successfully.

The route configuration therefore starts with:

```json
"replacement_green_receipt": null
```

The configuration audit remains invalid until a future reviewed change adds a
receipt from successful replacement runs.

## Components

### Scanner

The scanner reads `.github/workflows/*.yml` and `.yaml` using a non-coercing
YAML loader. It records:

- workflow name and path;
- trigger events;
- pull-request path filters;
- estimated job count from static matrix axes;
- concurrency declaration;
- workflow-dispatch and workflow-call availability;
- dynamic-matrix warnings.

The estimate is operational guidance, not GitHub scheduler truth.

### Admission report

For a supplied changed-file list, the report shows:

- workflows that appear eligible under legacy triggers;
- matching files and unfiltered triggers;
- estimated legacy jobs;
- selected replacement routes;
- selected shared validators;
- estimated replacement jobs;
- estimated reduction;
- hot path patterns shared by many workflows;
- route-config coverage status;
- immutable dry-run boundaries.

Path matching is deliberately labelled approximate because GitHub path-filter
semantics are the final authority.

### Problem Atlas routes

The current route table covers R0.3 through R0.11. Each route owns only:

- its module directory;
- its tests;
- its schemas;
- its documentation;
- its legacy workflow file.

A change to `omega_millennium_t/r11/model.py` selects only the R0.11 test
suite, not R0.3–R0.10.

### Shared CLI validator

`pyproject.toml` is not owned by every scientific route. It selects one shared
validator that statically checks each `[project.scripts]` entry point:

- module path exists;
- target attribute exists at top level;
- source parses as Python;
- no module is imported or executed.

This avoids waking every historical suite merely because one CLI entry was
added.

### Allowlisted runner

The runner accepts only:

```text
--kind route|validator
--id <configured identifier>
```

It resolves structured argument arrays from the reviewed JSON configuration,
expands only file globs, permits only `pytest` or `python`, rejects shell
fragments and executes with:

```text
shell = false
```

It cannot run an arbitrary command supplied by a pull request argument.

## Replacement workflow

`.github/workflows/omega-problem-atlas-router.yml` contains:

1. a planning job;
2. router self-tests;
3. changed-file collection;
4. dry-run fan-out report;
5. routed Python 3.10–3.13 suites;
6. one-job shared validators;
7. execution receipts;
8. an observation summary.

The plan report is uploaded as an artifact for 14 days.

## Commands

### Scan workflows

```bash
python -m omega_ci_admission_t.cli scan \
  --repository-root . \
  --output generated/omega_ci_admission/workflows.json
```

### Audit route coverage

```bash
python -m omega_ci_admission_t.cli audit-config \
  --repository-root . \
  --config config/omega_ci_admission/problem_atlas_routes.json
```

This command intentionally exits non-zero while the replacement green receipt
is missing.

### Simulate a stacked PR

```bash
cat > /tmp/changed-files.txt <<'EOF'
omega_millennium_t/r11/model.py
pyproject.toml
EOF

python -m omega_ci_admission_t.cli route \
  --repository-root . \
  --config config/omega_ci_admission/problem_atlas_routes.json \
  --changed-files-path /tmp/changed-files.txt \
  --output generated/omega_ci_admission/report.json
```

The expected replacement is:

```text
R0.11 scientific suite: 4 Python jobs
shared CLI validator:    1 job
```

It should not select R0.3–R0.10 solely because `pyproject.toml` changed.

## Migration phases

### Phase A — observation

- keep all legacy triggers unchanged;
- run the router in parallel;
- compare selected suites and outcomes;
- inspect missing and ambiguous coverage;
- measure estimated and actual queue reduction;
- record router failures in M−.

### Phase B — reviewed trigger migration

Only after repeated green receipts:

- update one legacy workflow at a time;
- preserve `workflow_dispatch` for manual deep validation;
- preserve required branch-protection check names or migrate protection rules;
- monitor missed-trigger counterexamples;
- maintain a rollback commit and documented restore procedure.

This PR implements only Phase A.

## Negative memory M−

The following are explicit failure modes:

- **M−CI1:** remove old workflows before replacement coverage is proven;
- **M−CI2:** treat a matrix estimate as exact scheduler usage;
- **M−CI3:** execute route commands through a shell;
- **M−CI4:** let shared files select every scientific suite;
- **M−CI5:** ignore unfiltered workflows;
- **M−CI6:** trust a route config that does not cover every scoped legacy file;
- **M−CI7:** declare the queue solved from a single green run;
- **M−CI8:** cancel unrelated user workflows automatically;
- **M−CI9:** change branch-protection checks without migration evidence;
- **M−CI10:** hide router uncertainty or path-matching approximation.

## OAK status

`CERTIFIED_CI_ADMISSION_OBSERVER_R0_1` may certify deterministic route
selection and dry-run boundaries after CI succeeds.

It does not certify:

- exact GitHub scheduler behavior;
- actual queue-time reduction before measured runs;
- safe legacy-trigger removal;
- complete repository-wide workflow coverage beyond configured scope;
- permission to cancel or rewrite unrelated workflows.
