# Ω-DOC-FACTORY-T∞ R1.0 — Evidence-Bound Documentation Factory

## Objective

R1.0 turns repository documentation into a compiled projection of versioned artifacts instead of a collection of repeated templates.

```text
repository snapshot
→ R0.3 structural scan
→ content-addressed AST/import enrichment
→ execution observations
→ explicit claim candidates
→ claim↔evidence review links
→ quality/staleness/delta
→ evidence graph
→ D0…D5 + JSON/JSONL + DOT/GraphML + LaTeX
→ OAK review
```

The source of truth remains the repository snapshot plus explicit observation receipts. Markdown, graphs and LaTeX are projections.

## Mandatory boundaries

```text
PATH_PRESENT != FUNCTIONAL_SYSTEM
MODULE_PRESENT != VALIDATED_BEHAVIOR
TEST_PRESENT != TEST_GREEN
WORKFLOW_PRESENT != CURRENT_CI_GREEN
DOC_GENERATED != SCIENTIFIC_TRUTH
CLAIM_DOCUMENTED != CLAIM_PROVEN
SIMULATION != MEASUREMENT
BENCHMARK_WIN != UNIVERSAL_SUPERIORITY
CI_GREEN != SCIENTIFIC_TRUTH
FORMAL_PROOF != PHYSICAL_VALIDATION
MERGED != INDEPENDENT_REPLICATION
FAMILY_CANDIDATE != SEMANTIC_EQUIVALENCE
EXECUTION_RECEIPT != INDEPENDENT_REPLICATION
GRAPH_CONNECTIVITY != CAUSALITY_OR_PROOF
CACHE_HIT != CURRENT_TRUTH
```

These are invariants, not warnings to remove later.

## Layering

R1.0 deliberately does **not** replace the green R0.3 scanner. `omega_latex_t.doc_universe` remains the low-level structural compiler. `omega_latex_t.doc_factory` adds the evidence campaign layer.

This gives a clean distinction:

```text
R0.3 = what repository structures exist?
R1.0 = what observations, claims, deltas and review relationships are attached to them?
```

## Content-addressed AST/import cache

R1.0 reparses observed Python modules only to extract import facts not present in R0.3. Results are cached by source SHA-256 under `imports-v1/<sha>.json`.

A cache hit is only an optimization. It cannot promote evidence or truth status.

The evidence graph emits an `imports` edge only when both source and target are observed repository modules. External dependencies are not invented as validated nodes.

## Execution receipts

Supported observation kinds:

- `test-run`;
- `workflow-run`;
- `benchmark-run`;
- `schema-validation`;
- `build-run`;
- `package-smoke`;
- `formal-proof`;
- `measurement`;
- `simulation`.

A receipt may bind to `artifact_path + source_sha256`. If the checkout no longer matches the recorded hash, R1.0 marks the observation `stale=true` with an explicit reason.

Every receipt has `authority=observation-only`.

A green test or workflow is evidence about that run in its recorded environment. It is not universal correctness and not scientific certification.

## Status tensor

R1.0 preserves the R0.3 status fields and adds independent axes rather than collapsing maturity into one label:

- `declared_system_status`;
- `documentation_status`;
- `evidence_status`;
- `oak_review_status`;
- `implementation_status`;
- `reproducibility_status`;
- `product_status`;
- `ip_status`.

Missing execution evidence cannot silently demote an externally demonstrated system, and rich documentation cannot silently promote an unvalidated claim.

## Claim compiler

R1.0 only extracts explicitly marked statements:

```text
Claim: ...
Affirmation: ...
Hypothesis: ...
Conjecture: ...
```

Arbitrary prose and headings are not auto-promoted to claims.

Every claim preserves source path, source line and source SHA-256. Its initial state is always:

```text
status = candidate-unverified
authority = documentation-observation
boundary = CLAIM_DOCUMENTED != CLAIM_PROVEN
```

## Claim↔evidence links

The compiler may attach a claim to structural surfaces or explicit execution receipts belonging to the same system. These links have:

```text
support_strength = unknown
authority = review-only
```

This prevents lexical/path association from becoming synthetic proof.

## Quality layer

Per system, R1.0 measures documentation/process properties such as:

- public API docstring ratio;
- structural evidence-category ratio;
- fresh/stale execution receipt counts;
- explicit claim candidate count;
- claims with review bindings;
- unresolved/TODO placeholder count.

These are documentation/evidence-surface metrics, not probabilities of truth.

## Fingerprints and semantic delta

Each system receives a deterministic fingerprint derived from:

- status tensor;
- module hashes;
- public API facts;
- internal import facts;
- structural receipt hashes;
- claim IDs;
- execution receipt IDs.

Comparing two factory reports yields:

- added systems;
- removed systems;
- changed systems;
- unchanged systems;
- previous documentation invalidated by observed changes.

`changed_systems` means the compiled evidence state changed. It does not prove behavioral or scientific impact.

## Evidence graph

The graph can contain:

- systems;
- modules;
- public symbols;
- observed internal import edges;
- execution receipts;
- claim candidates;
- review-only claim↔evidence links;
- generic structural evidence references.

Connectivity is not causality and is not proof.

## D0–D5

R0.3 D0–D5 remains the multi-resolution structural projection:

- D0 — compact identity/status;
- D1 — structural scope and evidence-surface counts;
- D2 — modules and source hashes;
- D3 — public API extracted by AST;
- D4 — structural receipts;
- D5 — OAK status/boundaries.

R1.0 stores execution observations, claims, delta, quality and graph projections beside the D0–D5 tree and joins them by `system_id`.

## Generated campaign bundle

```text
MANIFEST.json
factory-report.json
MASTER_DOC_ATLAS.md
quality.json
quality.csv
delta.json
claims.jsonl
claim-evidence-bindings.jsonl
execution-receipts.jsonl
graph/evidence-graph.json
graph/evidence-graph.dot
graph/evidence-graph.graphml
latex/MASTER_DOC_ATLAS.tex
depths/doc-universe.json
depths/systems/<system>/D0.md ... D5.md
```

The top-level manifest hashes every generated output.

## Determinism court

For the same checkout, explicit receipt payload and source commit, two campaigns must produce identical `MANIFEST.json` files.

CI executes this court on the real repository after the focused unit/adversarial tests.

## Promotion path

R1.0 intentionally stops before autonomous truth promotion.

A stronger status requires verifier-specific evidence:

```text
claim candidate
→ explicit obligation
→ named protocol/verifier
→ receipt
→ replay/reproduction
→ adversarial check/counterexample search
→ OAK decision
```

No amount of document volume, graph density, naming coherence or CI success substitutes for that chain.
