# Ω-TRANSFORMATION-IR R0.2 Architecture

## Purpose

The Transformation IR is the shared language between Intent, CreationDNA, experiments, PR Genome, evidence promotion and portfolio governance. It prevents each subsystem from inventing an incompatible representation of the same work.

## Data flow

```text
heterogeneous records
  → conservative adapters
  → typed IR nodes and edges
  → graph validation
  → bridge discovery
  → interface materialization
  → hard gates
  → portfolio selection
  → evidence bundle
```

## Modules

| Module | Responsibility |
|---|---|
| `contracts` | Stable IDs, enums, IR, constellations, decisions, manifests |
| `adapters` | Intent, CreationDNA, experiment, PR, portfolio and proof translation |
| `graph` | Type aliases, typed bridge search, closure and cycle analysis |
| `gates` | Non-compensatory OAK eligibility rules |
| `portfolio` | Budgeted and diversified selection |
| `proof` | Evidence validity, claim coverage and promotion assessment |
| `seed` | Six canonical strategic constellations |
| `kernel` | Deterministic orchestration |
| `manifest` | SHA-256/Merkle receipts, audit and bundle comparison |
| `cli` | Demo, compile, seed, audit and compare commands |

## Identity

Stable object IDs are SHA-256-derived from normalized structural inputs. Observation timestamps are excluded from the IR content digest. `SOURCE_DATE_EPOCH` provides reproducible bundle timestamps in CI.

## Type matching

Bridge discovery requires declared output-to-input compatibility. Exact and explicit alias matches score highest. Approximate mappings declare `semantic_type_approximation`; incomplete coverage declares `partial_consumer_type_coverage`.

Names are intentionally ignored as sufficient evidence. Two systems called “proof engine” do not compose unless their typed contracts align.

## Interface node

A discovered bridge materializes as a review-only interface node:

```json
{
  "mappings": {"repository_snapshot": "repository_snapshot"},
  "preserved_invariants": ["provenance", "authority", "uncertainty", "declared_losses"],
  "declared_losses": [],
  "review_only": true
}
```

The provider adapts to the interface; the interface resolves a consumer need. The interface cannot promote status or authority.

## Graph analytics

The graph supports:

- bounded impact closure;
- explicit relation filters;
- closure paths;
- strongly connected components;
- dependency-cycle detection;
- typed/evidence/provenance coverage;
- normalized interface entropy.

These are static structural analyses and may miss dynamic imports, runtime services and external organizational dependencies.

## Gate ordering

```text
structural validity
→ typed interface
→ baseline + simplest baseline
→ metric
→ falsifier
→ rollback
→ provenance
→ risk isolation
→ recursive governor
→ sensitive human gate
→ evidence threshold
→ human review eligibility
```

No weighted score can skip an earlier gate.

## Portfolio algorithm

Candidates are filtered by gate status and minimum utility. The selector uses a finite cost heuristic and rewards new domains plus satisfied dependencies. It respects:

- total budget;
- maximum items;
- maximum per primary domain;
- protected-domain coverage;
- deterministic tie-breaking.

The output is a plan, not authority.

## Determinism

For a fixed input, policy, source heads and `SOURCE_DATE_EPOCH`, two runs must produce:

- identical IR digest;
- identical artifact hashes;
- identical Merkle root;
- identical selected IDs;
- no changed artifact in `compare`.

## Extension contract

New adapters must:

1. accept a mapping or typed object;
2. emit explicit nodes and edges;
3. preserve source identity and provenance;
4. retain uncertainty and risk;
5. list warnings and declared losses;
6. never exceed A3;
7. include negative tests;
8. avoid remote mutations.

New object kinds, relations or score dimensions require schema updates and non-regression tests. Remote actuators remain outside this package behind separate authorization gates.
