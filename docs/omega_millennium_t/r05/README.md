# Ω-PROBLEM-ATLAS-T∞ R0.5 — Identity & Alias Graph

R0.5 converts R0.4 source imports into a conservative mathematical identity graph.
It addresses a central atlas risk: two catalogs may use different names for the
same problem, while two mathematically distinct variants may share exactly the
same title.

## OAK status

`CERTIFIED_IDENTITY_GRAPH_FIXTURE_R0_5` certifies only deterministic software
materialization and audit of supplied records. It does not certify that two
external formulations are mathematically equivalent, that a problem remains
open, that a proof is correct, or that a result is novel.

## Identity rules

An automatic merge is permitted only when all of the following agree:

1. normalized statement fingerprint;
2. mathematical front;
3. detected quantifier signature;
4. detected domain signature;
5. no explicit split receipt forbids the merge.

A manual merge requires an explicit decision receipt containing record IDs,
reason, reviewer identity, timestamp and evidence references.

The following never merge identities by themselves:

- equal titles;
- translated titles;
- declared aliases;
- token similarity;
- embeddings or future fuzzy scores;
- source popularity;
- an AI confidence value.

Fuzzy title matching produces only `possible_alias_review` candidate edges with
`identity_merge: false` and `requires_review: true`.

## Compile

```bash
omega-problem-identities compile \
  --import-jsonl generated/omega_problem_sources_r04/imports.jsonl \
  --output-dir generated/omega_problem_identities_r05
```

With reviewed decisions:

```bash
omega-problem-identities compile \
  --import-jsonl generated/omega_problem_sources_r04/imports.jsonl \
  --decision-json decisions/problem_identity_review.json \
  --output-dir generated/omega_problem_identities_r05
```

Audit:

```bash
omega-problem-identities audit generated/omega_problem_identities_r05
```

## Decision contract

```json
{
  "schema": "omega-problem-identity-decisions/5",
  "decisions": [
    {
      "decision_id": "merge-example-001",
      "action": "merge",
      "record_ids": [
        "record::source_a::problem_1::aaaaaaaaaaaaaaaa",
        "record::source_b::problem_2::bbbbbbbbbbbbbbbb"
      ],
      "canonical_record_id": "record::source_b::problem_2::bbbbbbbbbbbbbbbb",
      "reason": "A reviewed reference proves the formulations equivalent.",
      "decided_by": "named-reviewer-or-review-process",
      "decided_at": "2026-08-03T16:00:00Z",
      "evidence_refs": ["paper:theorem-4", "source:section-2"]
    }
  ]
}
```

Actions:

- `merge`: assert reviewed identity and join components;
- `split`: forbid direct and transitive merging;
- `alias`: connect terminology without joining identities.

A split receipt overrides automatic statement matching. A chain of manual
merges cannot bypass a split receipt: the compiler checks the complete
components before every union.

## Outputs

```text
source_records.jsonl
canonical_problems.jsonl
identity_edges.jsonl
alias_edges.jsonl
candidate_edges.jsonl
decision_receipts.jsonl
collision_quarantine.jsonl
identity_graph.graphml
manifest.json
report.json
```

### Source records

Preserve source-specific identifiers, title, aliases, statement, provenance,
statement fingerprint, quantifier signature and domain signature.

### Canonical problems

Contain deterministic membership, selected canonical source record, all known
titles and aliases, fronts and statement fingerprints. Every source record must
belong to exactly one canonical problem.

### Collision quarantine

Receives same-title/different-statement and source-identifier collisions.
Nothing in quarantine is silently repaired.

### GraphML

Exports source records, canonical problems, membership, reviewed identity
relations, alias relations and candidate review relations for external graph
analysis.

## Strict audit

The audit recalculates:

- SHA-256, byte and row receipts;
- manifest and report digests;
- source-record, canonical-record, decision, edge and collision digests;
- complete membership partition;
- all source/canonical references;
- split-decision compliance;
- merge-basis allowlist;
- report cardinalities;
- zero fuzzy merges;
- zero title-only merges;
- zero proof or solution claims.

## Scaling

R0.5 has no permanent total cap. Runtime storage, memory and CI budgets remain
finite campaign constraints. Future SQLite/streaming work should preserve the
same identity semantics and receipts rather than weakening them for scale.

## Next layer

R0.6 should attach claims, assumptions, theorems, counterexamples, barriers,
formal artifacts and computation receipts to these stable canonical identities.
