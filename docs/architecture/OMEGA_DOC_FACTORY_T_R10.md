# Ω-DOC-FACTORY-T∞ R1.0 — Architecture

## Component map

```text
                  ┌──────────────────────┐
                  │ Repository snapshot  │
                  └──────────┬───────────┘
                             │
                             ▼
          ┌────────────────────────────────────┐
          │ R0.3 doc_universe structural scan │
          │ systems / modules / API / receipts│
          └──────────┬─────────────────────────┘
                     │
        ┌────────────▼──────────────────────────┐
        │ R1.0 doc_factory campaign compiler   │
        ├───────────────────────────────────────┤
        │ content-addressed import AST cache    │
        │ execution receipt normalizer          │
        │ explicit claim extractor              │
        │ claim↔evidence review binder          │
        │ quality + placeholder audit           │
        │ fingerprints + delta                  │
        │ evidence/import graph                 │
        └──────────────┬────────────────────────┘
                       │
        ┌──────────────┼─────────────────────────────┐
        ▼              ▼              ▼              ▼
      JSON/JSONL      Markdown       Graphs         LaTeX
                       │
                       ▼
                 MASTER_DOC_ATLAS
```

## Scale model

The factory does not impose a fixed number of systems. Root `omega_*` discovery follows the checkout. Runtime is bounded only by physical runner resources, CI timeout, storage and safety constraints.

R0.3 already shares one repository inventory across system scans. R1.0 adds a SHA-addressed cache for its extra AST/import pass, so unchanged Python content can reuse previous import facts.

## Source versus generated state

The source repository is read-only to the compiler. Local writes are limited to:

- the configured cache directory;
- the configured output directory.

CI places both under `/tmp` for the full repository court, preventing generated output from becoming part of that court's source snapshot.

## Execution safety

The factory does **not** execute discovered repository tests, benchmarks or arbitrary commands. It ingests explicit receipts describing observations already made by an authorized runner or verifier.

This separates:

```text
repository discovery
!=
command execution
```

and prevents a documentation scan from becoming an implicit code-execution engine.

## Data flow

### Structural layer

R0.3 emits:

```text
System
  → modules
  → public_symbols
  → test/workflow/schema/doc/example/benchmark candidates
  → structural receipts
  → D0…D5
```

### R1.0 enrichment

R1.0 adds:

```text
System
  → internal imports
  → ExecutionReceipt*
  → ClaimCandidate*
  → ClaimEvidenceBinding*
  → QualityMetrics
  → Fingerprint
```

### Cross-system layer

```text
Systems + Modules + Claims + Receipts
→ EvidenceGraph
→ DOT / GraphML / JSON
```

## Execution receipt contract

Example input:

```json
{
  "receipts": [
    {
      "kind": "test-run",
      "system_id": "omega_latex_t",
      "artifact_path": "omega_latex_t/doc_factory.py",
      "source_sha256": "...",
      "status": "passed",
      "observed_at": "",
      "environment": {
        "python": "3.12"
      },
      "details": {
        "court": "focused-r03-r10"
      }
    }
  ]
}
```

The compiler derives a stable receipt ID, checks the artifact hash against the current checkout, and sets `stale`/`stale_reason`.

## Claim contract

Only explicit markers are compiled. The system intentionally does not perform broad semantic claim extraction in R1.0 because false-positive claims are more damaging than incomplete claim coverage.

A future semantic extractor may be added as a separate candidate layer, but it must never overwrite explicit claim status.

## Fingerprint contract

The system fingerprint includes facts that can invalidate generated documentation:

- statuses;
- module hashes;
- imports;
- API facts;
- structural receipts;
- claim IDs;
- execution receipt IDs.

A changed fingerprint invalidates the previous documentation snapshot for review. It does not assert that behavior changed.

## CI court

The GitHub Actions court runs Python 3.10–3.13 for focused validation.

All four versions:

1. compile R0.3/R1.0 modules and tests;
2. run R0.3 regression tests plus R1.0 courts;
3. validate JSON schemas;
4. verify CLI importability.

Python 3.12 additionally performs the expensive real-repository campaign:

1. create an explicit test-run observation receipt after tests have passed;
2. generate the entire factory bundle under `/tmp`;
3. validate `factory-report.json` against the R1.0 schema;
4. assert OAK boundaries and non-stale receipt state;
5. generate the same campaign a second time with the same inputs;
6. require byte-identical `MANIFEST.json`;
7. print measured campaign counts.

This avoids multiplying the full repository scan four times while retaining language-version compatibility testing.

## Failure semantics

Failures remain evidence:

- unreadable/syntax-invalid import AST → `import_residues`;
- stale execution hash → `stale=true`;
- unsupported receipt type → hard validation error;
- unknown receipt system → hard validation error;
- unmarked prose → no claim generated;
- changed fingerprint → previous documentation invalidated for review;
- missing evidence binding → claim remains candidate-unverified.

## OAK authority boundary

No generated artifact grants permission to:

- merge a PR;
- publish scientific claims;
- change repository permissions;
- decide IP disposition;
- declare a benchmark universally superior;
- declare a physical hypothesis validated;
- treat lexical family candidates as semantic equivalence.
