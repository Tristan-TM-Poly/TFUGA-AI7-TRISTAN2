# Ω-LATEX-T∞ — Evidence-bound scientific document compiler

**PR maturity:** R0.5 MAX prototype.  
**Authority:** review-only.  
**Core rule:** `LATEX != SOURCE_OF_TRUTH`.

Ω-LATEX-T∞ treats LaTeX as a deterministic projection of a typed semantic corpus rather than the primary truth store.

```text
sources / Markdown / SummaryBundle / GitHub event / machine results
→ DocumentIR
→ OAK audit
→ MathIR + notation + evidence routing
→ depth projection D^n
→ dependency sort
→ content-addressed fragment cache
→ LaTeX AST
→ deterministic .tex
→ optional TeX engine
→ evidence bundle
→ semantic ΔK → sharded/checkpointed ΔD plan
```

## R0.1 — DocumentIR and compiler

The canonical source object contains:

- document metadata;
- typed semantic nodes;
- dependencies;
- sources and provenance;
- result registry;
- notation declarations;
- OAK status;
- optional declared dimensions.

The compiler emits:

```text
document.tex
docir.json
oak-report.json
manifest.json
m_minus.jsonl
notation-registry.json
notation-rename-plan.json
evidence-matrix.json
```

The rendered LaTeX and the semantic input both receive SHA-256 identities.

## R0.2 — conservative adapters

Current offline adapters:

```text
Markdown → DocumentIR
omega_summary_fractal_t SummaryBundle → DocumentIR
normalized GitHub snapshot → DocumentIR
GitHub pull_request event payload → DocumentIR
machine result mapping → DocumentIR.results
```

Adapters do not silently promote:

```text
SUMMARY_EDGE → PROOF_DEPENDENCY
REPO_METADATA → SCIENTIFIC_TRUTH
REGISTERED_SOURCE → SUPPORTED_CLAIM
```

The PR event adapter only normalizes an already-received event. It performs no network access.

## R0.3 — MathIR and notation

Equations may now carry a structured `math_ir`.

Example:

```json
{
  "op": "eq",
  "lhs": {"op": "symbol", "name": "E"},
  "rhs": {
    "op": "mul",
    "args": [
      {"op": "symbol", "name": "m"},
      {
        "op": "pow",
        "base": {"op": "symbol", "name": "c"},
        "exp": {"op": "number", "value": 2}
      }
    ]
  }
}
```

With symbol units:

```text
E : J
m : kg
c : m/s
```

the stdlib-only unit algebra verifies

```text
[J] = [kg m^2 s^-2]
```

before rendering.

Supported R0.3 operators:

```text
symbol
number
add
sub
mul
div
pow
neg
eq
func(sin, cos, tan, exp, log, ln, sqrt, abs)
```

This is a bounded symbolic grammar, not a general CAS.

### Notation registry

Every declared symbol is indexed by:

```text
scope
symbol
meaning
unit
node IDs
```

Collisions produce reviewable rename proposals. The compiler never silently renames mathematical symbols.

## R0.4 — fractal depths and ΔK→ΔD

Nodes have optional:

```text
min_depth
max_depth
```

A default semantic policy projects a corpus into \(D^0,\ldots,D^n\). If a selected node requires a dependency outside the requested depth, the dependency is promoted into the projection and recorded in provenance.

Example:

```bash
omega-doc project corpus.json --depth 2 --output D2.json
omega-doc build-depths corpus.json --depths 0,1,2,3,4,5 --output-dir generated/depths
```

### Content-addressed fragment cache

Each rendered node fragment is keyed by:

```text
compiler cache version
node semantic hash
result key
current result value
```

Unchanged nodes can be reused without re-rendering.

```bash
omega-doc incremental-build corpus.json \
  --cache-dir .omega-latex-cache \
  --output-dir generated/current
```

With a previous corpus:

```bash
omega-doc incremental-build after.json \
  --before before.json \
  --cache-dir .omega-latex-cache \
  --output-dir generated/current
```

the semantic delta forces the affected structural closure while allowing unrelated cached fragments to survive.

### Rebuild plan

```bash
omega-doc rebuild-plan before.json after.json \
  --shard-size 128 \
  --output rebuild-plan.json
```

The plan contains:

```text
added
removed
changed
result drift
source drift
affected_after
shards
checkpoint
```

The finite shard size is execution policy, not an ontological ceiling. Higher-scale orchestration can route these shards through Ω-SANS-PLAFOND-T∞.

## R0.5 — theorem multi-projection

A theorem-like node can be projected into:

```text
theorem.json
theorem.tex
proof_graph.json
formal_stub.lean
numerical-test-contract.json
bundle-manifest.json
```

Example:

```bash
omega-doc theorem-bundle corpus.json \
  --theorem-id thm.demo \
  --output-dir generated/theorem-demo
```

Critical boundary:

```text
NARRATIVE_PROOF != FORMAL_PROOF
FORMAL_STUB != VERIFIED_PROOF
NUMERICAL_EVIDENCE != PROOF
PROOF_METADATA != INDEPENDENT_VERIFICATION
```

If Lean metadata is supplied, R0.5 deliberately emits a `sorry` proof obligation unless an external formal verifier later supplies a real checked proof. A generated stub can never promote theorem status.

## Evidence routing

`evidence-matrix.json` maps theorem/claim/result/experiment nodes to their registered sources and dependencies.

For strong statuses, a source can additionally be marked through metadata such as:

```json
{
  "support": [
    {
      "source": "src.paper",
      "relation": "supports",
      "reviewed": true
    }
  ]
}
```

This only records a review decision. It does not make citation entailment automatic.

## OAK gates

R0.5 detects or records:

- duplicate IDs;
- missing dependencies;
- dependency cycles;
- unknown provenance sources;
- malformed MathIR;
- dimensional contradictions discoverable inside the supported grammar;
- unknown symbol units as warnings;
- raw LaTeX balance failures;
- notation meaning/unit collisions;
- unsafe result keys;
- invalid depth ranges;
- theorem `proven` without a linked proof node;
- strong claims with no evidence path;
- registered but unreviewed source support.

## Determinism

A build manifest records:

```text
semantic_hash
latex_sha256
audit counts
compiler version
optional fragment-cache receipt
```

The CI double-builds the same fixture and byte-compares the resulting `.tex` and manifest.

## Current limitations

R0.5 does **not** prove:

- mathematical correctness of arbitrary theorems;
- truth of prose;
- complete physical-unit inference;
- semantic equivalence between natural language and MathIR;
- citation entailment;
- Lean/Coq/Isabelle verification;
- completeness of structural impact analysis;
- publisher-template compliance;
- PDF portability across every TeX distribution;
- infinite compute, storage, CI or review capacity;
- publication, merge, patent, legal or scientific authority.

## Canon laws

```text
LATEX != SOURCE_OF_TRUTH
TYPESETTING != PROOF
MATH_IR_VALID != THEOREM_TRUE
DIMENSIONALLY_CONSISTENT != PHYSICALLY_CORRECT
REGISTERED_SOURCE != SUPPORTED_CLAIM
REVIEWED_SUPPORT != INDEPENDENT_REPLICATION
SUMMARY_EDGE != PROOF_DEPENDENCY
REPO_METADATA != SCIENTIFIC_TRUTH
CACHE_HIT != CURRENT_TRUTH
AFFECTED_CLOSURE != COMPLETE_SEMANTIC_IMPACT
FORMAL_STUB != FORMAL_PROOF
SIMULATION != MEASUREMENT
GENERATED_DOCUMENT != PUBLICATION_AUTHORITY
```

## Next frontier

The next evidence-driven layers should be:

1. exact bibliography/citation-entry parsing;
2. source-fragment locators and claim-level quotation bounds;
3. formal-proof verifier adapters that ingest verifier receipts rather than self-certifying;
4. richer SI/non-SI unit grammar and uncertainty propagation;
5. TikZ/PGFPlots FigureIR;
6. GitHub Actions artifact publication for generated review PDFs;
7. repository-wide SummaryBundle → multi-depth monograph campaigns;
8. distributed cache/index integration with Ω-SANS-PLAFOND-T∞;
9. publisher/template backends as separate tested render targets;
10. content-addressed cross-document deduplication and a MetaDocumentGraph.
