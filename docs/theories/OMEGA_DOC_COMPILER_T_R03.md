# Ω-DOC-COMPILER-T R0.3 — Evidence-Bound Documentation

## Problem

The R0.2 mass documentation experiment proved that a complete D0–D5 *shape* can be generated cheaply, but also exposed a critical debt:

```text
template coverage != repository understanding
file count != information density
documentation generated != evidence resolved
```

A documentation system becomes useful when its statements are derived from versioned artifacts and their limitations remain explicit.

## R0.3 objective

Compile documentation from observable repository facts:

```text
checkout
→ root-system discovery
→ safe file inventory
→ Python AST
→ public API facts
→ test candidates
→ workflow candidates
→ schema/doc/example/benchmark candidates
→ evidence receipts
→ separate status axes
→ D0…D5 projections
→ content-addressed manifest
```

## Four status axes

R0.3 forbids collapsing maturity into one ambiguous field:

1. `declared_system_status` — S/E/X/D/C/A or another externally supplied status.
2. `documentation_status` — how much structure was actually resolved.
3. `evidence_status` — whether structural evidence surfaces were found.
4. `oak_review_status` — review/promotion state.

A documented system is not demoted merely because the documentation scanner has not resolved its evidence. Conversely, a rich document cannot promote a scientific claim.

## D0–D5 semantics

- D0 — compact identity and measured structural counts.
- D1 — structural role and evidence-surface counts.
- D2 — module map with source SHA-256.
- D3 — public API extracted from Python AST.
- D4 — structural evidence receipts.
- D5 — OAK boundaries, review state and lexical family candidates.

R0.3 intentionally does **not** claim:
- a test candidate ran;
- a workflow is green;
- a benchmark proves superiority;
- two family candidates are semantically equivalent;
- a generated claim is scientifically true.

## Family candidates

Lexical family grouping is explicitly only a review candidate:

```text
omega_auto2
omega_auto2_kernel
omega_auto2_p0
```

may belong to one family, but repository naming alone does not prove semantic equivalence or supersession.

## CLI

```bash
python -m omega_latex_t.doc_universe_cli . \
  --source-commit "$(git rev-parse HEAD)" \
  --output-dir generated/omega_doc_universe
```

Optional declared statuses:

```bash
python -m omega_latex_t.doc_universe_cli . \
  --declared-statuses statuses.json \
  --output-dir generated/omega_doc_universe
```

## Next OAK steps

R0.4 should resolve *run receipts*, not merely config presence:

- test execution receipts;
- GitHub Actions run/job receipts;
- benchmark protocol + environment + observations;
- formal proof receipts;
- claim↔evidence bindings;
- git/PR/release lineage;
- stale-document detection;
- doc delta per PR.

## Boundaries

```text
PATH_PRESENT != FUNCTIONAL_SYSTEM
MODULE_PRESENT != VALIDATED_BEHAVIOR
TEST_PRESENT != TEST_GREEN
WORKFLOW_PRESENT != CURRENT_CI_GREEN
DOC_GENERATED != SCIENTIFIC_TRUTH
CLAIM_DOCUMENTED != CLAIM_PROVEN
SIMULATION != MEASUREMENT
```
