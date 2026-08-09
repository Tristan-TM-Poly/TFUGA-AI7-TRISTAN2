# Ω-LATEX-T∞ — Evidence-bound scientific document compiler

**PR maturity:** R0.8 MAX prototype.  
**Authority:** review-only.  
**Core law:** `LATEX != SOURCE_OF_TRUTH`.

Ω-LATEX-T∞ compiles a typed semantic corpus into reviewable documents while keeping evidence, uncertainty, figures and formal-verifier receipts distinct from claims of truth.

```text
local/authorized sources
→ DocumentIR
→ OAK audit
→ MathIR + Unit/Uncertainty + FigureIR
→ claim-level source locators
→ depth projections D^0…D^n
→ fragment cache + ΔK→ΔD rebuild plan
→ LaTeX AST
→ deterministic document.tex + evidence sidecars
→ optional external formal-verifier receipts
→ MetaDocumentGraph / universe campaign
```

## R0.1–R0.5 retained

R0.1 introduced typed DocumentIR, deterministic LaTeX lowering and OAK gates. R0.2 added conservative Markdown/SummaryBundle/GitHub adapters and semantic delta. R0.3 added bounded MathIR, SI-style unit algebra, notation registry and evidence routing. R0.4 added fractal depth projections, proof/dependency closure, content-addressed fragment cache and sharded rebuild plans. R0.5 added theorem multi-projection with a deliberately unproved Lean `sorry` stub.

## R0.6 — bibliography and exact evidence locators

`Source` now supports structured metadata and each semantic node can carry `source_locators`, so the evidence edge is no longer merely `claim → paper`; it can be `claim → paper:Sec.4/Eq.7/page 12/commit abc`. A bounded BibTeX parser accepts literal fields, rejects duplicate keys and macro concatenation, and converts entries into registered sources. Parsing bibliographic metadata is not external verification.

Builds emit `bibliography-report.json` and LaTeX `thebibliography` entries. Strong claims without a useful source locator receive an OAK warning.

## R0.6 — FigureIR → TikZ/PGFPlots

Figure nodes may carry a bounded `figure_ir` rather than arbitrary TikZ text. Current kinds are:

- `graph`: finite nodes, coordinates, edges and labels;
- `plot`: finite numeric series with line/scatter/line+markers modes.

The renderer rejects unsafe identifiers, non-finite values and invalid edge endpoints. FigureIR validates the rendering contract only: `RENDERABLE_FIGURE != VALID_DATA`.

## R0.7 — uncertainty as a first-class result object

A result may be a structured measurement:

```json
{"value": 12.5, "uncertainty": 0.4, "unit": "m", "method": "std", "coverage": 0.95}
```

LaTeX renders `value ± uncertainty` and `uncertainty-ledger.json` records the measurement contract. A small independent-error propagation kernel supports add/subtract, multiplication and division under explicit assumptions. It does not infer correlation, distribution or calibration.

## R0.7 — external verifier receipts

Bare metadata such as `formal_verified=true` no longer certifies a theorem. Formal verification requires an external receipt for Lean, Coq or Isabelle whose `statement_sha256` matches the exact formal statement, with optional artifact hash matching. The theorem bundle records the receipt separately and only then reports `verified-external-receipt`.

```text
FORMAL_STUB != FORMAL_PROOF
FORMAL_RECEIPT != NATURAL_LANGUAGE_EQUIVALENCE
FORMAL_RECEIPT != SCIENTIFIC_TRUTH
```

## R0.8 — MetaDocumentGraph

Multiple DocumentIR objects can be compiled into a structural MetaDocumentGraph. It reports:

- exact content duplicate candidates;
- `canonical_key` conflict candidates;
- orphan candidates;
- source usage and shared-source edges.

These are navigation/review signals. A conflict candidate is not automatically a logical contradiction.

## R0.8 — `build-universe`

A finite manifest of local/authorized inputs can generate all requested document-depth jobs with shared content-addressed cache and checkpoint/resume:

```bash
omega-doc universe-plan examples/omega_latex_t_universe_manifest.json
omega-doc build-universe examples/omega_latex_t_universe_manifest.json \
  --output-dir generated/omega_latex_universe \
  --cache-dir .omega-latex-universe-cache
```

The manifest can contain hundreds or thousands of entries. There is no hard-coded total-document ceiling; each run remains finite and bounded by actual resources, quality gates and explicit input scope. No network access, GitHub mutation, publication or merge occurs inside `build-universe`.

## R0.8 build sidecars

```text
document.tex
docir.json
oak-report.json
manifest.json
m_minus.jsonl
notation-registry.json
notation-rename-plan.json
evidence-matrix.json
bibliography-report.json
figure-manifest.json
uncertainty-ledger.json
verifier-receipts.json
```

## OAK canon

```text
LATEX != SOURCE_OF_TRUTH
TYPESETTING != PROOF
MATH_IR_VALID != THEOREM_TRUE
DIMENSIONALLY_CONSISTENT != PHYSICALLY_CORRECT
REGISTERED_SOURCE != SUPPORTED_CLAIM
SOURCE_LOCATOR != ENTAILMENT
BIBTEX_PARSED != SOURCE_VERIFIED
REVIEWED_SUPPORT != INDEPENDENT_REPLICATION
FIGURE_RENDERED != DATA_VALIDATED
UNCERTAINTY_FIELD != CALIBRATED_UNCERTAINTY
CACHE_HIT != CURRENT_TRUTH
AFFECTED_CLOSURE != COMPLETE_SEMANTIC_IMPACT
FORMAL_STUB != FORMAL_PROOF
VERIFIER_RECEIPT != NATURAL_LANGUAGE_EQUIVALENCE
META_CONFLICT_CANDIDATE != CONTRADICTION
UNIVERSE_BUILD_SUCCESS != PUBLICATION_READINESS
SIMULATION != MEASUREMENT
GENERATED_DOCUMENT != PUBLICATION_AUTHORITY
```

## Next frontier

R0.9+ should focus on verified source-fragment ingestion, DOI/Crossref metadata receipts without treating metadata as truth, richer covariance-aware uncertainty, SVG/PDF figure backends, external proof-artifact adapters, publisher-specific backends as separately tested targets, distributed cache indexes, GitHub-wide SummaryBundle manifests and MetaDocumentGraph dashboards.
