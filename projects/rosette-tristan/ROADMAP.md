# Ω-ROSETTE-T Roadmap

## Phase 0 — MVP pushed

- [x] Local CLI scaffold: `rosette ingest`, `extract`, `compile`
- [x] TXT extraction and optional PDF text extraction through PyMuPDF
- [x] Heuristic equation extraction with span/source trace
- [x] LaTeX fragment generation
- [x] theory/claim graph seed
- [x] code skeleton generation with `NotImplementedError` safety
- [x] absorption capsule
- [x] OAK report and M⁻ output
- [x] CI workflow scoped to `projects/rosette-tristan/`

## Phase 1 — Rosette Fidelity

- [ ] Add page-level PDF source refs and bbox-compatible schema
- [ ] Add extractor adapters: Marker, Docling, GROBID, Mathpix/Nougat-compatible import format
- [ ] Add consensus engine across extractors
- [ ] Add block confidence tensor: text/layout/math/table/figure/citation/code/theory/repro
- [ ] Add render-diff-repair loop for equations and tables

## Phase 2 — Theory Compiler

- [ ] Build claim-evidence graph with explicit equation/table/figure/reference links
- [ ] Detect definitions, assumptions, limits and variables
- [ ] Add Equation Dimensional OAK hooks
- [ ] Add contradiction and missing-evidence detector
- [ ] Export `theory_capsule.yaml`

## Phase 3 — Code/Reproduction

- [ ] Translate simple ODE/algebraic equations to executable Python stubs
- [ ] Add figure-to-code reproduction statuses
- [ ] Add unit tests generated from limiting cases
- [ ] Add notebooks for paper reproduction
- [ ] Add benchmark runner

## Phase 4 — RosetteBench

- [ ] Create benchmark fixtures: math-heavy, table-heavy, two-column, old scan, patent, physics/materials
- [ ] Metrics: text WER/CER, equation exact/semantic, table F1, claim grounding, code execution, OAK honesty
- [ ] Baseline against PyMuPDF-only extraction

## Phase 5 — IP/Productization

- [ ] Add license/citation classification
- [ ] Add confidential/private mode
- [ ] Add `Paper → GitHub` compiler with issue generation
- [ ] Add Quebec papers/patents vertical search integration

## OAK lock

No source extraction is truth until source refs, confidence, reproduction status and failure modes are preserved.
