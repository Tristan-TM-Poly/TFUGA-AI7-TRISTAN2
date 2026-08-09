# Ω-LATEX-T∞ — Evidence-bound scientific document compiler

## Status

`R0.1 / EXECUTABLE_SEED / OAK-REVIEW`

Ω-LATEX-T∞ treats LaTeX as a deterministic projection of a semantic document graph rather than as the canonical knowledge store.

```text
sources
→ Knowledge/Document IR
→ dependency audit
→ LaTeX AST
→ deterministic .tex
→ optional TeX engine
→ evidence bundle
→ M⁻ residuals
```

## R0.1 executable contract

The canonical input is `DocumentIR`: metadata, typed semantic nodes, dependency edges, registered sources, symbol declarations, optional dimensional signatures, executable result values and provenance.

The first vocabulary includes sections, definitions, axioms, conjectures, lemmas, propositions, theorems, proofs, equations, algorithms, experiments, datasets, results, figures, tables, claims, warnings, open questions, counterexamples and appendices.

The compiler lowers typed nodes into a small LaTeX AST (`Command`, `Environment`, `Text`, `Raw`, `Sequence`) instead of asking a generator to emit an unconstrained `.tex` file.

## OAK gates

R0.1 checks unique semantic IDs, missing dependencies, dependency cycles, missing provenance identifiers, unbalanced equation braces/environments, explicit dimension-signature mismatches, symbol collisions, unsafe executable-result keys, evidence warnings for strong statuses, and proof linkage for theorems marked `proven`.

A warning is not silently promoted to a proof. A named theorem is not a theorem merely because it is typeset in a theorem environment.

## Evidence bundle

`omega-doc build` emits:

```text
document.tex
docir.json
oak-report.json
manifest.json
m_minus.jsonl
```

The manifest carries both the semantic input hash and rendered LaTeX hash for content-addressed regeneration and later PR→document delta tracking.

## Executable results

Results live in `DocumentIR.results` and become deterministic `\Result{key}` macros, so benchmark values can be injected from machine-readable ledgers rather than copied manually. Automatic benchmark-ledger ingestion is a planned adapter, not yet claimed as implemented.

## OAK boundary

R0.1 proves only software properties covered by deterministic audits and tests. It does not yet prove general theorem correctness, semantic truth of prose, complete dimensional analysis, source entailment, Lean/Coq equivalence, publisher-template correctness, or autonomous publication authority.

## Next layers

- **R0.2 adapters:** Markdown/README, `omega_summary_fractal_t`, GitHub repository/PR, benchmark ledgers, BibTeX/Crossref.
- **R0.3 semantic lint:** symbolic equation AST, unit algebra, notation scopes, limit tests, claim↔source review hooks.
- **R0.4 incremental graph:** node content addressing, dependency-aware rebuild, `ΔK → ΔD`, semantic diff, sharding/checkpoints through Ω-SANS-PLAFOND-T∞.
- **R0.5 proof projections:** one theorem object may project to `theorem.json`, `paper.tex`, `theorem.lean`, `numerical_test.py`, and `proof_graph.json`, while keeping formal proof distinct from heuristic evidence.

## Canon rule

```text
LATEX != SOURCE_OF_TRUTH
TYPESETTING != PROOF
REGISTERED_SOURCE != SUPPORTED_CLAIM
SIMULATION != MEASUREMENT
GENERATED_DOCUMENT != PUBLICATION_AUTHORITY
```
