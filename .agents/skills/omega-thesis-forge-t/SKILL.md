---
name: omega-thesis-forge-t
description: Build a research-monograph-grade LaTeX thesis from Tristan GitHub repositories, PRs, code, tests, benchmarks, documents, claims, negative memory, and external scholarly literature, with a compiled 512-page default target, claim/evidence ledgers, OAK gates, uncertainty, reproducibility, and bidirectional theory-to-code traceability. Use when the user asks for a thesis, dissertation, monograph, habilitation-style manuscript, or long-form research synthesis grounded in their GitHub corpus.
---

# Ω-THESIS-FORGE-T∞ — GitHub-to-Thesis Research Compiler

Treat a thesis as a **proof-carrying research artifact**, not as long-form prose.

## Canonical transformation

```text
TOPIC / QUESTION
→ GITHUB CORPUS DISCOVERY
→ SOURCE / CLAIM / EVIDENCE LEDGERS
→ STATE-OF-THE-ART GAP MAP
→ FORMAL CONTRIBUTION GRAPH
→ EXPERIMENT / BENCHMARK PROGRAM
→ 512-PAGE LATEX ARCHITECTURE
→ CHAPTER COMPILATION
→ CROSS-CHAPTER CONSISTENCY
→ LATEX BUILD
→ PAGE CONTROLLER
→ OAK / UNC² / M− REVIEW
→ REPRODUCIBILITY BUNDLE
→ THESIS CANDIDATE
```

For Tristan systems preserve:

```text
Theory ⇄ ExecutableSystem
       ↓ semantic diff
Claims ⇄ Code ⇄ Tests ⇄ Benchmarks ⇄ Evidence
       ↓
OAK + UNC² + M+/M−/M?
```

## Primary objective

Produce a coherent LaTeX manuscript whose **compiled PDF is exactly 512 pages by default**, unless the user explicitly chooses another target.

The 512-page target must be reached through scientific information density:

- deeper mathematical formalization;
- broader and more precise state-of-the-art comparison;
- explicit proofs, derivations and counterexamples;
- architecture definitions and semantic contracts;
- implementation mappings;
- reproducible experiments and benchmark courts;
- ablations and negative controls;
- uncertainty and causal analysis;
- failure cases and M−;
- appendices containing reproducibility and formal details.

Never use page inflation as a substitute for content.

“Post-doctorat+++” means **research-monograph rigor**, not inflated certainty.

## Activation

Use when the user asks to:

- create a 512-page LaTeX thesis grounded in their GitHub work;
- synthesize many repositories, PRs, theories, tests and benchmarks into one scientific manuscript;
- turn a Tristan theory into an academic monograph;
- build an executable thesis linking claims to code/tests/benchmarks;
- update a thesis after GitHub changes while preserving provenance;
- audit whether a manuscript is actually supported by its repository evidence.

Do not activate for short essays, README files, formatting-only LaTeX questions, or requests to fabricate citations/results.

## Invariant 0 — SEARCH → REUSE → ADAPT → GENERATE

Before any substantial new chapter:

1. search the authorized GitHub corpus;
2. reuse existing theories, code, figures, tests, benchmarks, schemas, PR reasoning and documentation;
3. adapt only when necessary;
4. generate new prose/formalization/experiments only after reuse search.

Never begin with `GENERATE → maybe SEARCH`.

## Phase A — Thesis contract

Create `thesis_contract.json` before prose.

Minimum contract:

```json
{
  "title": "...",
  "language": "fr",
  "target_pages_total": 512,
  "page_tolerance": 0,
  "document_class": "book",
  "paper": "letterpaper",
  "font_size": "11pt",
  "bibliography_engine": "biber",
  "citation_style": "numeric-comp",
  "topic": "...",
  "central_question": "...",
  "thesis_claim": "...",
  "scope_in": [],
  "scope_out": [],
  "required_repositories": [],
  "required_external_literature": true,
  "compiled_page_count_is_source_of_truth": true
}
```

If the user supplies a source PDF/topic only, infer a **candidate** title and central question, label the inference, and continue unless ambiguity changes the research object materially.

## Phase B — GitHub corpus compiler

Search across:

1. repositories and descriptions;
2. canonical docs/theory cards;
3. source code and schemas;
4. tests/property tests;
5. benchmarks and outputs;
6. open PRs;
7. merged/closed PRs;
8. issues/design discussions;
9. relevant commits;
10. CI/workflows;
11. M+, M− and M? artifacts;
12. generated artifacts with status preserved.

Build `corpus_manifest.jsonl` with repository, path/PR, exact SHA when available, artifact type, topic tags, claim IDs, evidence type, status, provenance and reuse priority.

Repository naming or README presence is not evidence by itself.

## Phase C — Claim–Evidence Ledger

Every nontrivial claim gets a stable ID such as:

```text
CLM-FORMAL-001
CLM-ARCH-014
CLM-EXP-027
CLM-LIMIT-004
```

Each row records:

```text
claim_id
text
class = definition|derived|implemented|measured|simulated|hypothesis|conjecture|external-established
status = SUPPORTED|PARTIAL|UNSUPPORTED|FALSIFIED|HOLD
github_anchors
literature_anchors
tests
benchmarks
uncertainty
counter_hypothesis
limitations
```

Hard rules:

- `test passed != scientific claim proven`;
- `code exists != method is novel`;
- `simulation agrees != experiment validated`;
- `visual pattern != theorem`;
- `internal terminology != established terminology`;
- `generated candidate != accepted contribution`;
- `citation exists != citation supports the exact claim`.

## Phase D — Literature and novelty court

For each claimed contribution:

```text
Contribution
→ nearest prior art
→ shared structure
→ material difference
→ why difference matters
→ supporting evidence
→ limitations
→ falsification route
```

Create `novelty_matrix.csv`.

If external literature access is incomplete, retain explicit gaps. Never fabricate bibliography entries or novelty claims.

## Phase E — Formalization compiler

Map each core construct to a formal card:

```text
Name
Domain
Definition
Symbols
Units/types
Assumptions
Axioms
Operators
Invariants
Boundary conditions
Propositions
Proof status
Counterexamples
Computational representation
Experimental interpretation
Known prior art
OAK status
```

Use theorem environments only when justified. A conjecture, numerical pattern or simulation is never silently promoted to theorem.

For HGFM, CVCD, OAK, UNC², LLMT, Capability IR, Repo Algebra, WorkUnit, EvidenceReceipt, GO MAX and other Tristan constructs, explicitly map them against established concepts before any novelty wording.

## Phase F — Theory ⇄ Code bidirectional traceability

Build both directions:

```text
Theory → formal object → implementation → test → benchmark → evidence
Code → implicit assumptions → mathematical model → thesis claim → limitations
```

Create `traceability_matrix.jsonl` linking chapter/section, claim ID, repo, path, symbol/function, test, benchmark, commit SHA and literature reference.

Theory/implementation mismatch becomes an OAK defect.

## Phase G — Experiment compiler

Every empirical study must declare:

1. research question;
2. null/baseline hypothesis;
3. dataset/generator provenance;
4. preprocessing;
5. units/semantics;
6. baselines;
7. metrics;
8. uncertainty/statistics;
9. negative controls;
10. ablations;
11. seeds/configuration;
12. failure analysis;
13. compute cost;
14. threats to validity.

Missing evidence becomes a benchmark/experiment plan, not fictional results.

## Phase H — 512-page architecture

The **compiled PDF page count** is the source of truth.

Default information budget:

```text
Front matter                                   24
Part I — Problem, prior art, foundations       48
Part II — Formal mycelial systems calculus     84
Part III — Architecture and compilers          84
Part IV — Evidence, trust, OAK and UNC²        72
Part V — Learning, evolution and self-hosting  60
Part VI — Experiments and case studies         80
Part VII — Synthesis and conclusion            24
Bibliography                                   24
Appendices                                     12
TOTAL                                         512
```

These are control targets, not padding quotas.

Never reach 512 by:

- blank pages inserted solely for count;
- duplicated text;
- inflated spacing;
- oversized low-information figures;
- artificial chapter fragmentation;
- verbose paraphrase of the same claim.

Use the extra 256 pages to **increase research depth**, especially formal proofs, literature comparison, benchmark breadth, ablations, uncertainty, failure analysis, traceability and reproducibility.

## Phase I — LaTeX architecture

Prefer:

```text
thesis/
├── main.tex
├── config/
├── frontmatter/
├── chapters/
├── appendices/
├── figures/
├── tables/
├── algorithms/
├── bibliography/references.bib
├── evidence/
│   ├── corpus_manifest.jsonl
│   ├── claims_ledger.jsonl
│   ├── traceability_matrix.jsonl
│   ├── novelty_matrix.csv
│   └── oak_report.json
├── scripts/
│   ├── build.sh
│   ├── page_controller.py
│   └── check_claims.py
└── Makefile
```

Avoid dependency proliferation and require reproducible compilation.

## Phase J — Chapter compiler

Every chapter follows:

```text
Question
→ Context / prior art
→ Definitions
→ Method / construction
→ Formal properties
→ Implementation mapping
→ Evidence / experiment
→ Failure modes
→ Limitations
→ Chapter synthesis
→ Forward dependencies
```

Maintain a hidden or visible chapter audit with claims supported/partial/falsified, open questions, GitHub anchors, literature anchors, artifacts and next falsification step.

## Phase K — Page Controller

After each full build:

1. measure actual PDF pages;
2. compute `delta = 512 - actual_pages`;
3. rank candidate expansions/compressions by marginal scientific information value;
4. modify highest-value sections;
5. rebuild;
6. repeat until exactly 512 pages unless user tolerance differs.

Never infer page count from word count alone.

If no TeX engine is available, set the page gate to `HOLD/UNVERIFIED` and emit exact build instructions rather than pretending the target was achieved.

## Phase L — Cross-chapter consistency court

Check symbols, notation, units/types, acronym expansions, terminology, claim status, equation semantics, references, bibliography keys, labels, chapter conclusions, abstract and conclusion.

The abstract/conclusion may never exceed the evidence strength in the claim ledger.

## Phase M — OAK thesis gate

Minimum gates:

```text
G0  LaTeX structural compile
G1  references/cross-references
G2  bibliography integrity
G3  claim→evidence coverage
G4  GitHub provenance/SHA anchoring
G5  theory↔code semantic consistency
G6  experiment reproducibility
G7  uncertainty/statistics
G8  novelty/prior-art wording
G9  negative-results/limitations
G10 theorem/scientific-discovery language
G11 compiled page-count = 512
G12 artifact hashes/manifest
```

`PROMOTE_CANDIDATE` requires every must-pass gate to PASS. HOLD is preferable to fabricated certainty.

## Phase N — M+, M−, M? thesis memory

```text
M+ = verified reusable arguments, experiments, figures, proofs, code mappings
M− = falsified claims, failed derivations, broken builds, negative benchmarks, rejected novelty claims
M? = promising but unresolved hypotheses, missing experiments, literature ambiguities
```

M− is preserved even when inconvenient to the narrative.

## Phase O — Default specialization for TTM-GitHub-001

Use `references/default_profile_mycelial_github.md`.

Research progression:

```text
Repo
→ RepoCell / CapabilityCell
→ Capability IR
→ Executable Hypergraph / HGFM
→ Repo Algebra
→ Intent-to-RepoGraph / Repo Compiler
→ Theory ⇄ ExecutableSystem
→ Proof-Carrying Repositories
→ Semantic / Scientific CI
→ OAK / UNC² / M+/M−/M?
→ Evolution / self-hosting
→ Mycelial Systems Calculus
```

Treat mycelium, embryogenesis, mitosis, apoptosis, metabolism and horizontal gene transfer as architectural metaphors/models unless formal semantics is supplied.

## Output contract

A complete run emits at least:

1. modular `thesis/main.tex` tree;
2. bibliography database;
3. `thesis_contract.json`;
4. `corpus_manifest.jsonl`;
5. `claims_ledger.jsonl`;
6. `traceability_matrix.jsonl`;
7. `novelty_matrix.csv`;
8. experiment/benchmark manifests;
9. `oak_report.json`;
10. M+/M−/M? ledgers;
11. reproducible build instructions;
12. compiled PDF when tooling permits;
13. page-count receipt proving the 512-page target.

## Definition of done

Done requires:

- precise central question and bounded scope;
- material GitHub contributions anchored to exact evidence;
- external scholarship separated from internal evidence;
- prior-art comparison for major contributions;
- empirical claims supported or explicitly pending;
- theorem/conjecture/observation status correctness;
- visible negative evidence and limitations;
- reproducible source/build/evidence artifacts;
- actual compiled PDF page count measured;
- **exactly 512 pages by default**;
- final abstract/conclusion no stronger than the evidence ledger.

## OAK invariants

- 512 pages is a compiled artifact property, not a prose estimate.
- Quantity of pages is never a proxy for scientific quality.
- GitHub provenance is not peer review.
- A merged PR is not proof of scientific correctness.
- An unmerged PR may contain useful evidence but remains draft evidence.
- Code/tests support implementation claims, not novelty by themselves.
- Benchmarks require baselines, configurations, uncertainty and provenance.
- Tristan terminology must be mapped to standard literature concepts before novelty language.
- No citation, experimental result, theorem proof or novelty claim may be fabricated.
- Failed attempts and negative results remain available as M−.
- External writes, merges, publication, releases and IP actions remain separately authorized.
- The final manuscript must be auditable from claims back to exact GitHub/literature evidence.
