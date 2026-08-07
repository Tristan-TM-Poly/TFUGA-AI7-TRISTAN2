# Ω-PROBLEM-ATLAS-T∞ R0.6 — Claim–Evidence–Barrier Hypergraph

R0.6 attaches scientific and mathematical evidence to the stable canonical
problem identities produced by R0.5. It separates a statement being mentioned,
numerically supported, proved in a restricted scope, kernel-checked in general,
and independently reviewed.

## OAK status

`CERTIFIED_CLAIM_EVIDENCE_FIXTURE_R0_6` certifies deterministic software
materialization and audit for supplied fixtures. It does not certify theorem
correctness, mathematical truth, novelty, current problem status, journal
acceptance, prize eligibility or solution of an open problem.

## Node types

- `claim` — a scoped assertion requesting a promotion status;
- `evidence` — numerical, symbolic, exact, experimental, literature or proof text;
- `assumption` — a dependency that must be discharged or retained explicitly;
- `barrier` — a known obstruction or limitation of a method;
- `counterexample` — a restricted or general falsifying object;
- `computation_receipt` — a reproducible run result with immutable digest;
- `formal_artifact` — a restricted or general proof object;
- `independent_review` — an accepted, challenged or rejected external review.

Every node must preserve a canonical problem identity, source references,
timezone-aware observation time, exact scope and a cryptographic digest.

## Relations

```text
supports
contradicts
scopes
specializes
generalizes
depends_on
discharges
violates
proves_restricted_case
improves_bound
reproduces
merely_mentions
```

`merely_mentions` is intentionally separate from evidential support.
Cross-problem edges fail closed except explicit `generalizes` or `specializes`
relations with `cross_problem_relation: true`.

## Promotion ladder

```text
candidate
→ experimental
→ restricted_result
→ formal_restricted
→ general_proof_candidate
→ kernel_checked_general
→ independently_reviewed_general
```

Promotion is blocked by:

- undischarged assumptions;
- active barriers;
- counterexamples or contradictory evidence;
- challenged or rejected reviews;
- insufficient evidence for the requested status;
- attempts to derive a general proof from numerical evidence.

Core invariant:

```text
numerical evidence ≠ general mathematical proof
```

A kernel-checked general artifact can reach `kernel_checked_general`; independent
accepted review is additionally required for `independently_reviewed_general`.

## Compile

```bash
omega-problem-evidence compile \
  --canonical-problems generated/omega_problem_identities_r05/canonical_problems.jsonl \
  --bundle-json evidence/campaign_001.json \
  --output-dir generated/omega_problem_evidence_r06
```

Audit:

```bash
omega-problem-evidence audit generated/omega_problem_evidence_r06
```

## Bundle contract

```json
{
  "schema": "omega-problem-evidence-bundle/6",
  "bundle_id": "campaign-001",
  "nodes": [],
  "edges": []
}
```

Multiple bundles may be compiled together. Bundle IDs, node IDs and edge IDs
must be unique.

### Computation receipt requirements

A computation receipt requires:

- `outcome`: `success`, `failure`, `timeout`, `invalid_certificate` or `diverged`;
- immutable `run_digest`;
- Boolean `certificate_verified` when present;
- environment, inputs and replay metadata through normal metadata fields.

A certificate verifier remains conceptually separate from its generator.

### Formal artifact requirements

A formal artifact requires:

- `proof_scope`: `restricted` or `general`;
- Boolean `kernel_checked`;
- named `verifier` whenever `kernel_checked` is true.

### Review requirements

An independent review requires:

- `outcome`: `accepted`, `challenged` or `rejected`;
- reviewer/process identifier;
- exact review scope;
- source references.

### Counterexample requirements

A counterexample declares `counterexample_scope` as `restricted` or `general`.
Its independent verification status is stored separately and never inferred.

## Outputs

```text
canonical_identity_refs.jsonl
bundle_receipts.jsonl
nodes.jsonl
edges.jsonl
claim_assessments.jsonl
mminus_records.jsonl
evidence_graph.graphml
manifest.json
report.json
```

The evidence graph is cryptographically tied to the R0.5 canonical identity
records through `canonical_identity_refs.jsonl` and a combined input digest.

## M− negative memory

The following become immutable M− records:

- barriers;
- counterexamples;
- failed, timed-out, diverged or invalid-certificate computations;
- challenged or rejected independent reviews;
- `contradicts` and `violates` relations.

M− prevents a later campaign from silently forgetting known failures or
repeating invalid promotion paths.

## Strict audit

The audit recalculates:

- all file receipts and manifest/report digests;
- node and edge digests;
- typed edge semantics;
- canonical identity references;
- every claim assessment from nodes and edges;
- every M− record;
- all report cardinalities;
- zero numerical-to-general-proof promotions;
- zero mathematical-truth probability claims;
- zero solution claims.

## Next layer

R0.7 should compile selected evidence work cells into isolated exact,
SAT/SMT, interval, symbolic, numerical and proof-assistant jobs with replayable
receipts and independently verifiable certificates.
