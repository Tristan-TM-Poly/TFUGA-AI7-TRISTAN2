# Ω-LATEX-T∞ — Evidence-bound scientific document factory

**PR maturity:** R1.0 MAX prototype.  
**Authority:** review-only.  
**Core law:** `LATEX != SOURCE_OF_TRUTH`.

Ω-LATEX-T∞ compiles a typed semantic corpus into deterministic, reviewable documents while keeping source identity, evidence, uncertainty, figures, formal verification and publication authority separate.

```text
local/authorized sources + repository snapshots + machine results
→ immutable source-fragment receipts
→ DocumentIR
→ OAK audit
→ MathIR + units + covariance + FigureIR
→ claim-level evidence locators
→ depth projections D^0…D^n
→ fragment cache + ΔK→ΔD rebuild plan
→ LaTeX/TikZ + deterministic SVG
→ evidence/proof/provenance sidecars
→ MetaDocumentGraph + human review queue
→ repository inventory → universe manifest
→ sharded/checkpointed document campaigns
```

## R0.1–R0.5 — compiler foundations

R0.1 introduced typed DocumentIR, deterministic LaTeX lowering and OAK gates. R0.2 added conservative Markdown/SummaryBundle/GitHub adapters and semantic delta. R0.3 added bounded MathIR, SI-style unit algebra, notation registry and evidence routing. R0.4 added fractal depth projections, proof/dependency closure, content-addressed fragment cache and sharded rebuild plans. R0.5 added theorem multi-projection with a deliberately unproved Lean `sorry` stub.

## R0.6 — bibliography, locators and FigureIR

`Source` supports structured metadata and nodes carry `source_locators`, so an evidence edge can target `paper:Sec.4/Eq.7/page 12/commit abc` rather than just a paper-level identifier. The bounded BibTeX parser remains metadata ingestion, not source verification.

Figure nodes use bounded `FigureIR` (`graph` and numeric `plot`) rather than arbitrary TikZ. TikZ/PGFPlots rendering validates rendering structure only.

## R0.7 — uncertainty and external verifier receipts

Structured results can carry value, uncertainty, unit, method and coverage. Independent first-order propagation remains available, without inferring distributions or calibration.

Formal theorem status cannot be promoted by `formal_verified=true`. A Lean/Coq/Isabelle verifier receipt must match theorem ID, exact formal-statement SHA-256, verifier result and optional artifact SHA-256.

## R0.8 — MetaDocumentGraph and build-universe

MetaDocumentGraph emits duplicate, canonical-key conflict, orphan and shared-source candidates. These are review signals, not semantic verdicts.

`build-universe` compiles finite manifests across requested depths with shared content-addressed cache, sharding and checkpoint/resume. There is no hard-coded total-document ceiling; each actual run is finite and resource-bounded.

## R0.9 — immutable source fragments

R1.0 adds a first content-level provenance primitive:

```text
source bytes
→ source_sha256
→ exact line range
→ fragment bytes
→ fragment_sha256
→ SourceFragmentReceipt
```

A receipt records source ID, exact line locator, source hash, fragment hash, byte count and encoding. OAK verifies that the source is registered and, when `Source.sha256` is known, that the receipt source hash matches it.

This closes an important gap between `claim → source ID` and `claim → immutable source fragment identity` while preserving the boundary:

```text
SOURCE_FRAGMENT_HASH_MATCH != CLAIM_ENTAILMENT
```

The compiler never needs network access to create or verify these receipts.

## R0.9 — metadata receipts without truth promotion

Already-retrieved Crossref/DataCite/OpenAlex/manual metadata can be normalized into deterministic receipts containing raw and normalized SHA-256 hashes. DOI syntax is normalized, but metadata existence never upgrades claim status.

```text
DOI_METADATA_RECEIPT != PEER_REVIEW
DOI_METADATA_RECEIPT != REPRODUCIBILITY
DOI_METADATA_RECEIPT != CLAIM_TRUTH
```

No remote DOI lookup is performed inside the compiler.

## R0.9 — covariance-aware uncertainty

A document may register named covariance models in provenance. R1.0 validates finite square symmetric covariance matrices, variable cardinality and non-negative diagonal terms, then supports:

- scalar linear propagation `u² = gᵀΣg`;
- multi-output Jacobian propagation `Σ_y = JΣ_xJᵀ`;
- deterministic covariance ledgers.

This is algebraic propagation under supplied assumptions. It does not certify calibration, stationarity, covariance estimation quality or model adequacy.

## R0.9 — deterministic SVG backend

FigureIR now has a second renderer in addition to TikZ/PGFPlots: a standard-library deterministic SVG backend for bounded graph/plot figures. Each render receives a `spec_sha256` and `artifact_sha256` receipt.

```text
SVG_HASH_MATCH != DATA_VALIDATED
SVG_RENDER_SUCCESS != SCIENTIFIC_CORRECTNESS
```

PDF remains an external render-engine concern rather than being falsely claimed as universally available.

## R1.0 — proof lineage

Verifier receipts are now projected into an explicit lineage graph:

```text
theorem
→ verifier receipt
→ proof artifact hash
→ optional parent receipt
```

This records how formal evidence artifacts relate across runs. Missing parent receipts are OAK findings. Lineage does not prove that a natural-language theorem was formalized correctly or that the verifier environment itself is trustworthy.

## R1.0 — repository inventory → universe compiler

An already-authorized normalized repository inventory can be transformed into an Ω-LATEX universe manifest. A repository is admitted only when it explicitly declares a local/authorized `document_source` path.

Repository metadata stays in a separate routing table; compilable manifest entries remain compatible with the existing universe schema. Repositories without an authorized document source are skipped with a reason rather than guessed.

```text
REPOSITORY_EXISTS != DOCUMENT_SOURCE_AUTHORIZED
REPOSITORY_METADATA != SCIENTIFIC_EVIDENCE
```

This is the bridge required for GitHub-wide SummaryBundle/DocIR campaigns without embedding GitHub credentials or network mutation into the compiler.

## R1.0 — sharded content-addressed cache index

A deterministic cache index maps explicit keys to SHA-256-addressed content and prefix shards. The index detects key collisions with different content and emits its own content hash. This is a routing layer suitable for later distributed storage adapters.

```text
CACHE_IDENTITY != CURRENT_TRUTH
```

Semantic/environment inputs still belong in caller-generated cache keys.

## R1.0 — MetaDocument review queue

Structural candidates from MetaDocumentGraph are converted into a deterministic human review queue:

1. canonical-key conflict candidate;
2. exact duplicate candidate;
3. orphan candidate.

Priority is workflow ordering only. The queue does not declare contradiction, plagiarism, novelty, equivalence or error.

## R1.0 build sidecars

Normal builds now emit:

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
figure-backends.json
uncertainty-ledger.json
covariance-ledger.json
verifier-receipts.json
proof-lineage.json
source-fragments.json
metadata-receipts.json
```

## R1.0 CLI surfaces

In addition to the retained compiler commands:

```text
source-fragment
attach-source-fragment
source-fragments
metadata-receipt
attach-metadata-receipt
metadata-receipts
attach-covariance-model
covariance
covariance-linear
covariance-jacobian
figure-svg
proof-lineage
universe-from-repos
cache-index
metadocument-review
```

All operate on local/already-authorized artifacts. They do not mutate GitHub, publish documents or contact external metadata/proof services.

## OAK canon

```text
LATEX != SOURCE_OF_TRUTH
TYPESETTING != PROOF
MATH_IR_VALID != THEOREM_TRUE
DIMENSIONALLY_CONSISTENT != PHYSICALLY_CORRECT
REGISTERED_SOURCE != SUPPORTED_CLAIM
SOURCE_LOCATOR != ENTAILMENT
SOURCE_FRAGMENT_HASH_MATCH != CLAIM_ENTAILMENT
BIBTEX_PARSED != SOURCE_VERIFIED
METADATA_RECEIPT != CLAIM_TRUTH
REVIEWED_SUPPORT != INDEPENDENT_REPLICATION
FIGURE_RENDERED != DATA_VALIDATED
SVG_HASH_MATCH != DATA_VALIDATED
UNCERTAINTY_FIELD != CALIBRATED_UNCERTAINTY
COVARIANCE_PROPAGATED != COVARIANCE_VALIDATED
CACHE_HIT != CURRENT_TRUTH
CACHE_INDEXED != CURRENT_TRUTH
AFFECTED_CLOSURE != COMPLETE_SEMANTIC_IMPACT
FORMAL_STUB != FORMAL_PROOF
VERIFIER_RECEIPT != NATURAL_LANGUAGE_EQUIVALENCE
PROOF_LINEAGE != SPECIFICATION_CORRECTNESS
META_CONFLICT_CANDIDATE != CONTRADICTION
REVIEW_QUEUE_PRIORITY != TRUTH_PRIORITY
REPOSITORY_METADATA != SCIENTIFIC_TRUTH
UNIVERSE_BUILD_SUCCESS != PUBLICATION_READINESS
SIMULATION != MEASUREMENT
GENERATED_DOCUMENT != PUBLICATION_AUTHORITY
```

## Next frontier after R1.0

The next evidence-driven layer should focus on immutable binary/PDF fragment locators, normalized external metadata adapters executed outside the pure compiler, covariance estimation provenance, SVG→PDF renderer receipts, formal proof environment/container hashes, repository-level SummaryBundle discovery, distributed object-store adapters, publisher profiles as separately tested render targets and interactive MetaDocumentGraph review dashboards.
