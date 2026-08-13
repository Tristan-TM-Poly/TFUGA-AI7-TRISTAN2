---
name: omega-thesis-forge-t
description: Build a research-monograph-grade LaTeX thesis from Tristan GitHub repositories, PRs, code, tests, benchmarks, documents, claims, negative memory, and external scholarly literature, with a compiled 256-page target, claim/evidence ledgers, OAK gates, uncertainty, reproducibility, and bidirectional theory-to-code traceability. Use when the user asks for a thesis, dissertation, monograph, habilitation-style manuscript, or long-form research synthesis grounded in their GitHub corpus.
---

# Ω-THESIS-FORGE-T∞ — GitHub-to-Thesis Research Compiler

Treat a thesis as a **proof-carrying research artifact**, not as long-form prose.

The canonical transformation is:

```text
TOPIC / QUESTION
→ GITHUB CORPUS DISCOVERY
→ SOURCE / CLAIM / EVIDENCE LEDGERS
→ STATE-OF-THE-ART GAP MAP
→ FORMAL CONTRIBUTION GRAPH
→ EXPERIMENT / BENCHMARK PROGRAM
→ 256-PAGE LATEX ARCHITECTURE
→ CHAPTER COMPILATION
→ CROSS-CHAPTER CONSISTENCY
→ LATEX BUILD
→ PAGE CONTROLLER
→ OAK / UNC² / M− REVIEW
→ REPRODUCIBILITY BUNDLE
→ THESIS CANDIDATE
```

For Tristan systems, preserve the higher-order loop:

```text
Theory ⇄ ExecutableSystem
       ↓ semantic diff
Claims ⇄ Code ⇄ Tests ⇄ Benchmarks ⇄ Evidence
       ↓
OAK + UNC² + M+/M−/M?
```

## Primary objective

Produce a coherent LaTeX manuscript whose **compiled PDF is 256 pages by default**, with publication-grade mathematics, algorithms, experiments, source provenance, scholarly references, falsification paths, reproducibility metadata, and a precise distinction between:

- established external science;
- known prior art;
- Tristan definitions and constructions;
- derived propositions;
- implemented software;
- measured results;
- simulations;
- conjectures;
- speculative but fertile hypotheses;
- unsupported claims that must be downgraded or removed.

“Post-doctorat+++” is interpreted operationally as **research-monograph rigor**: deep literature positioning, formal objects, explicit assumptions, theorem/proof or proposition/derivation boundaries, reproducible experiments, adversarial falsification, limitations, and contribution-level traceability. It is never interpreted as permission to inflate certainty.

## Activation

Use this skill when the user asks to:

- create a 256-page LaTeX thesis from their GitHub work;
- synthesize many repositories/PRs into one scientific manuscript;
- turn a Tristan theory into an academic monograph;
- create an executable thesis where claims link to code/tests/benchmarks;
- produce a thesis scaffold and iteratively fill it from GitHub evidence;
- rebuild or update a thesis after GitHub changes;
- audit whether an existing manuscript is supported by repository evidence.

Do not activate for:

- a short essay, ordinary report, README, blog post, or presentation;
- a literature review with no GitHub/research-corpus component;
- formatting-only LaTeX help;
- requests to fabricate experimental results or citations.

## Invariant 0 — SEARCH → REUSE → ADAPT → GENERATE

Before drafting any chapter:

1. search the authorized GitHub corpus;
2. reuse existing theories, code, figures, tests, benchmarks, schemas, PR reasoning, and documentation;
3. adapt only when necessary;
4. generate genuinely new prose, formalization, experiments, or glue only after reuse search.

Never begin with `GENERATE → maybe SEARCH`.

## Phase A — Thesis contract

Create `thesis_contract.json` before prose.

Minimum fields:

```json
{
  "title": "...",
  "language": "fr",
  "target_pages_total": 256,
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

If the user supplies only a source PDF/topic, infer a **candidate** title/question from it, label the inference, and continue without blocking unless the ambiguity materially changes the research object.

## Phase B — GitHub corpus compiler

Use GitHub read tools to discover the smallest sufficient but evidence-rich corpus.

Search across:

1. repositories and repository descriptions;
2. canonical docs and theory cards;
3. source code and schemas;
4. tests and property tests;
5. benchmarks and benchmark outputs;
6. open PRs;
7. merged/closed PRs;
8. issues and design discussions;
9. recent and historically important commits;
10. CI/workflow definitions when methodological claims depend on them;
11. M+, M− and M? artifacts when present;
12. generated artifacts only with their provenance/status preserved.

Build `corpus_manifest.jsonl` with at least:

```text
repo
path_or_pr
commit_or_head_sha
artifact_type
topic_tags
claim_ids
evidence_type
status
provenance
reuse_priority
```

A repository name or README mention is not evidence by itself. Prefer code/tests/benchmarks/merged history for implementation claims and authoritative literature for external scientific claims.

## Phase C — Claim–Evidence Ledger

Every nontrivial thesis claim receives a stable identifier, for example:

```text
CLM-FORMAL-001
CLM-ARCH-014
CLM-EXP-027
CLM-LIMIT-004
```

Store in `claims_ledger.jsonl`:

```json
{
  "claim_id": "CLM-ARCH-001",
  "text": "...",
  "class": "definition|derived|implemented|measured|simulated|hypothesis|conjecture|external-established",
  "status": "SUPPORTED|PARTIAL|UNSUPPORTED|FALSIFIED|HOLD",
  "github_anchors": [],
  "literature_anchors": [],
  "tests": [],
  "benchmarks": [],
  "uncertainty": {},
  "counter_hypothesis": "...",
  "limitations": []
}
```

Hard rules:

- `test passed != scientific claim proven`;
- `code exists != method is novel`;
- `simulation agrees != experiment validated`;
- `visual pattern != theorem`;
- `internal terminology != established literature terminology`;
- `generated candidate != accepted contribution`;
- `citation exists != citation supports the exact claim`.

## Phase D — Literature and novelty court

A research-monograph-grade thesis requires external scholarship in addition to GitHub.

For each claimed contribution, construct:

```text
Contribution
→ nearest prior art
→ difference
→ why difference matters
→ evidence
→ limitations
→ falsification route
```

Create `novelty_matrix.csv` or equivalent with columns:

```text
contribution_id
tristan_construct
nearest_prior_art
shared_structure
material_difference
novelty_status
evidence_required
risk_of_overclaim
```

If external web/paper access is unavailable, leave literature gaps explicit. Never replace missing scholarship with model memory presented as verified bibliography.

## Phase E — Formalization compiler

For mathematical/theoretical material, map each object into a formal card:

```text
Name
Domain
Definition
Symbols
Units / types
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

Use theorem environments only when appropriate:

```latex
\newtheorem{definition}{Definition}[chapter]
\newtheorem{theorem}[definition]{Theorem}
\newtheorem{proposition}[definition]{Proposition}
\newtheorem{lemma}[definition]{Lemma}
\newtheorem{conjecture}[definition]{Conjecture}
```

Never typeset a conjecture or numerical observation as a theorem.

For Tristan-specific names such as HGFM, CVCD, OAK, UNC², LLMT, Capability IR, Repo Algebra, WorkUnit, EvidenceReceipt, or GO MAX, introduce them as explicit constructions and position them against established concepts rather than assuming novelty from naming.

## Phase F — Theory ⇄ Code bidirectional traceability

Build both directions:

```text
Theory → formal object → implementation → test → benchmark → evidence
```

and

```text
Code → implicit assumptions → mathematical model → thesis claim → limitations
```

Create `traceability_matrix.jsonl` linking:

```text
chapter/section
claim_id
repo
path
symbol_or_function
test
benchmark
commit_sha
literature_reference
```

A semantic mismatch between theory and implementation becomes an OAK defect, not something to smooth over in prose.

## Phase G — Experiment compiler

Every empirical chapter must include:

1. research question;
2. null/baseline hypothesis;
3. dataset or synthetic generator provenance;
4. preprocessing;
5. units and semantics;
6. baselines;
7. metrics;
8. uncertainty/statistics;
9. negative controls;
10. ablations;
11. reproducibility seed/config;
12. failure analysis;
13. compute cost;
14. threats to validity.

Prefer executable measurements already present in GitHub. If evidence is missing, generate an **experiment plan or benchmark harness**, not fictional results.

## Phase H — 256-page architecture

The compiled PDF page count is the source of truth.

Default total budget:

```text
Front matter                                  12
Part I — Problem, prior art, foundations      24
Part II — Formal mycelial systems calculus    42
Part III — Architecture and compilers         42
Part IV — Evidence, trust, OAK and UNC²       36
Part V — Learning, evolution and self-hosting 30
Part VI — Experiments and case studies        40
Part VII — Synthesis and conclusion           12
Bibliography                                  12
Appendices                                     6
TOTAL                                         256
```

These are control targets, not padding quotas.

Never reach 256 pages by:

- blank pages inserted solely for count;
- oversized figures/tables with no information gain;
- duplicated text;
- inflated spacing;
- artificial chapter breaks;
- verbose paraphrase of the same claim.

Reach the target by increasing or compressing **scientific information density**: proofs, derivations, literature comparisons, ablations, diagrams, pseudocode, benchmark tables, failure analyses, appendices, and reproducibility material.

## Phase I — LaTeX architecture

Prefer a modular tree:

```text
thesis/
├── main.tex
├── config/
│   ├── packages.tex
│   ├── macros.tex
│   ├── theorem-envs.tex
│   └── metadata.tex
├── frontmatter/
│   ├── abstract-fr.tex
│   ├── abstract-en.tex
│   ├── acknowledgements.tex
│   └── nomenclature.tex
├── chapters/
│   ├── ch01.tex
│   └── ...
├── appendices/
├── figures/
├── tables/
├── algorithms/
├── bibliography/
│   └── references.bib
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

Recommended packages when justified:

```text
amsmath, amssymb, mathtools, bm
microtype, booktabs, longtable, tabularx
siunitx
algorithm2e or algorithmicx
cleveref, hyperref
csquotes, biblatex
xcolor
listings or minted when shell-escape is acceptable
pgfplots/tikz only when native vector diagrams materially help
```

Avoid dependency proliferation. A thesis must compile in a reproducible environment.

## Phase J — Chapter compiler

Each chapter should follow a research pattern rather than generic prose:

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

At the end of every chapter emit an internal audit table:

```text
Claims supported
Claims partial
Claims falsified
Open questions
GitHub anchors
External references
Artifacts produced
Next falsification step
```

This table may be hidden from the final typeset version if desired, but must remain in the evidence bundle.

## Phase K — Page Controller

After every full LaTeX build:

1. obtain actual page count from the compiled PDF;
2. compute `delta = 256 - actual_pages`;
3. identify underdeveloped or overlong scientific sections using the claim/evidence ledger;
4. expand or compress content with highest marginal information value;
5. rebuild;
6. repeat until the compiled PDF is exactly 256 pages, unless the user sets a tolerance.

Never infer page count from word count alone.

If a TeX engine is unavailable, mark page control `UNVERIFIED` and produce the best bounded estimate plus the exact build command required for validation.

## Phase L — Cross-chapter consistency court

Check globally:

- symbols defined once and used consistently;
- acronym expansion and glossary consistency;
- terminology stability;
- same claim never receives incompatible statuses;
- definitions do not silently change by chapter;
- equations preserve units/types;
- figure/table references resolve;
- bibliography keys resolve;
- no orphan labels;
- chapter conclusions match evidence;
- abstract and conclusion do not overclaim beyond body evidence.

## Phase M — OAK thesis gate

Minimum gates:

```text
G0  LaTeX structural compile
G1  reference/cross-reference integrity
G2  bibliography integrity
G3  claim→evidence coverage
G4  GitHub provenance and SHA anchoring
G5  theory↔code semantic consistency
G6  experiment reproducibility
G7  uncertainty/statistics adequacy
G8  novelty/prior-art wording
G9  negative-results and limitations presence
G10 no unsupported theorem/scientific discovery language
G11 compiled page-count target
G12 artifact hashes / manifest
```

Output `oak_report.json` with PASS/HOLD/FAIL per gate and actionable defects.

A thesis candidate is `PROMOTE_CANDIDATE` only when all must-pass gates are PASS. HOLD is preferable to fabricated certainty.

## Phase N — M+, M−, M? thesis memory

Preserve:

```text
M+ = verified reusable arguments, experiments, figures, proofs, code mappings
M− = falsified claims, failed derivations, broken builds, negative benchmarks, rejected novelty claims
M? = promising but unresolved hypotheses, missing experiments, literature ambiguities
```

Do not delete M− from the evidence bundle merely because it weakens the narrative. Negative knowledge is part of the scientific contribution.

## Phase O — Default specialization for TTM-GitHub-001

When the supplied source is the TTM-GitHub-001 architecture, use the default profile in `references/default_profile_mycelial_github.md`.

The research object is the progression:

```text
Repo
→ RepoCell / CapabilityCell
→ Capability IR
→ Executable Hypergraph / HGFM
→ Repo Algebra
→ Intent-to-RepoGraph / Repo Compiler
→ Theory ⇄ ExecutableSystem
→ Proof-Carrying Repositories
→ Scientific CI / OAK / UNC²
→ Evolution / self-hosting
→ Mycelial Systems Calculus
```

Treat biological vocabulary such as mycelium, embryogenesis, mitosis, apoptosis, metabolism, or horizontal gene transfer as **architectural metaphors/models** unless a precise formal semantics is supplied.

## GitHub read policy

Use GitHub reads aggressively for grounding. Prefer:

```text
repo metadata
→ search code/docs
→ fetch exact files
→ inspect PR/commit history
→ inspect tests/benchmarks
→ build anchored evidence ledger
```

For changing repository state, preserve the real approval boundary. A thesis-generation skill does not grant write, merge, publication, release, or IP-disclosure authority.

## Output contract

A complete run should produce, at minimum:

1. `thesis/main.tex` and modular chapter files;
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
12. compiled PDF when the execution environment supports it;
13. actual page-count receipt proving the 256-page target.

## Definition of done

The skill is done only when:

- the thesis has a precise central question and bounded scope;
- all material GitHub contributions have source anchors;
- external scholarship is separated from internal GitHub evidence;
- every major contribution has a prior-art comparison;
- all empirical claims have real evidence or are explicitly marked pending;
- theorem/conjecture/observation statuses are correct;
- negative evidence and limitations are visible;
- source, build, and evidence artifacts are reproducible;
- the compiled PDF page count is actually measured;
- the measured total equals 256 pages by default;
- the final abstract/conclusion contain no claim stronger than the evidence ledger permits.

## OAK invariants

- 256 pages is a compiled artifact property, not a prose estimate.
- Quantity of pages is never a proxy for scientific quality.
- GitHub provenance is not peer review.
- A merged PR is not proof of scientific correctness.
- An unmerged PR may contain useful evidence but must retain draft status.
- Code and tests support implementation claims, not novelty by themselves.
- Benchmarks require baselines, configurations, uncertainty, and provenance.
- Internal Tristan terminology must be mapped to standard literature concepts before novelty language.
- No citation is fabricated.
- No experimental result is fabricated.
- No theorem is promoted without a proof or clearly declared proof status.
- Failed attempts and negative results remain available as M−.
- External writes/publication/IP actions remain separately authorized.
- The final manuscript must be auditable from thesis claims back to exact GitHub/literature evidence.
