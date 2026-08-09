# Ω-LATEX-T∞ — Evidence-bound scientific document compiler

## Status

`R0.2 / EXECUTABLE / OAK-REVIEW`

Ω-LATEX-T∞ treats LaTeX as a deterministic projection of a semantic document graph rather than as the canonical knowledge store.

```text
sources → Knowledge/Document IR → dependency audit → LaTeX AST → deterministic .tex → optional TeX engine → evidence bundle → M⁻ residuals
```

## R0.1 executable contract

The canonical input is `DocumentIR`: metadata, typed semantic nodes, dependency edges, registered sources, symbol declarations, optional dimensional signatures, executable result values and provenance. The compiler lowers typed nodes into a constrained LaTeX AST (`Command`, `Environment`, `Text`, `Raw`, `Sequence`) rather than generating an unconstrained `.tex` file.

## OAK gates

R0.1 checks unique semantic IDs, missing dependencies, dependency cycles, missing provenance identifiers, unbalanced equation braces/environments, explicit dimension-signature mismatches, symbol collisions, unsafe executable-result keys, evidence warnings for strong statuses, and proof linkage for theorems marked `proven`.

## Evidence bundle

`omega-doc build` emits `document.tex`, `docir.json`, `oak-report.json`, `manifest.json`, and `m_minus.jsonl`. The manifest carries both semantic input and rendered LaTeX hashes.

## Executable results

Results live in `DocumentIR.results` and become deterministic `\Result{key}` macros. Automatic scientific interpretation of a benchmark remains outside R0.2.

## R0.2 adapter layer

Implemented conservative adapters:

```text
Markdown -> DocumentIR
omega_summary_fractal_t SummaryBundle -> DocumentIR
authorized normalized GitHub snapshot -> DocumentIR
machine result registry -> DocumentIR.results
DocumentIR_before + DocumentIR_after -> semantic delta + dependent rebuild closure
```

The SummaryBundle adapter preserves arbitrary graph edges as provenance metadata rather than relabeling every relation as a proof dependency. The GitHub adapter performs no network access; acquisition remains an explicitly authorized connector responsibility.

`semantic_delta()` computes added, removed and content-changed nodes, then expands changed nodes through the reverse dependency closure. This is the first executable `ΔK → ΔD` seed; it is structural, not a claim of complete semantic impact detection.

## OAK boundary

R0.2 does not prove general theorem correctness, semantic truth of prose, complete dimensional analysis, source entailment, Lean/Coq equivalence, publisher-template correctness, or autonomous publication authority.

## Next layers

- **R0.3 semantic lint:** symbolic equation AST, unit algebra, notation scopes, limit tests, claim↔source review hooks.
- **R0.4 incremental graph:** node content addressing, dependency-aware rebuild, PR event adapters, cache/sharding/checkpoints through Ω-SANS-PLAFOND-T∞.
- **R0.5 proof projections:** one theorem object may project to `theorem.json`, `paper.tex`, `theorem.lean`, `numerical_test.py`, and `proof_graph.json`, while formal proof remains distinct from heuristic evidence.

## Canon rule

```text
LATEX != SOURCE_OF_TRUTH
TYPESETTING != PROOF
REGISTERED_SOURCE != SUPPORTED_CLAIM
SIMULATION != MEASUREMENT
GENERATED_DOCUMENT != PUBLICATION_AUTHORITY
```
