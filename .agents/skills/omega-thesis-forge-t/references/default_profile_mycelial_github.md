# Default thesis profile — TTM-GitHub-001 / Ω-MYCELIAL-SYSTEMS-CALCULUS-T

## Target

**512 compiled LaTeX pages, exact by default.**

The page count is measured from the built PDF. This profile never treats word count or source-file length as proof of the target.

## Candidate title

**Calcul mycélien des écosystèmes logiciels et scientifiques distribués : hypergraphes exécutables, représentation intermédiaire des capacités, compilation bidirectionnelle théorie–code et validation épistémique**

English working title:

**A Mycelial Calculus for Distributed Software–Scientific Ecosystems: Executable Hypergraphs, Capability Intermediate Representations, Bidirectional Theory–Code Compilation, and Evidence-Carrying Validation**

This is a candidate title, not a novelty claim.

## Research object

The manuscript studies a GitHub-scale research ecosystem not as a bag of repositories but as a multiscale executable system in which repositories, modules, functions, capabilities, claims, evidence, tests, benchmarks, agents, transformations and histories are typed objects linked by executable hyperedges.

The source architecture progresses through:

```text
Repo
→ RepoCell
→ CapabilityCell
→ Capability IR
→ Dynamic Capability Graph
→ Executable Hyperedges / HGFM
→ Repo Algebra
→ Intent-to-RepoGraph Compiler
→ Theory-to-Repo / Repo-to-Theory Compiler
→ Proof-Carrying Repository
→ Semantic / Scientific CI
→ OAK + UNC² + M+/M−/M?
→ Self-hosting / Meta-evolution
→ Mycelial Systems Calculus
```

## Central research question

> Can a large, heterogeneous and evolving research-code ecosystem be represented and operated as a typed multiscale hypergraph of capabilities such that composition, reuse, evidence propagation, semantic consistency and controlled self-improvement become explicit, testable and scalable properties rather than ad-hoc repository conventions?

## Candidate thesis statement

A hypothesis to test, not assume:

> A capability-centered, typed, multiscale executable-hypergraph architecture can reduce coordination friction and increase reusable verified composition in large research-code ecosystems when semantic contracts, evidence propagation, routing, lifecycle operations and self-improvement mechanisms are subjected to explicit global invariants, reproducible benchmarks, uncertainty tracking and falsification gates.

## OAK thesis stance

The manuscript must distinguish:

```text
known external result
internal definition
formal derivation
implemented mechanism
simulation
measured result
hypothesis
conjecture
negative result
unsupported claim
```

Internal Tristan terminology is not itself evidence of novelty. GitHub implementation is not peer review. Passing tests are not scientific proof. Biological vocabulary such as mycelium, mitosis, apoptosis and metabolism is treated as an architectural model/metaphor until given formal semantics.

# Exact 512-page information budget

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

The budget is a control surface, not a padding quota.

# Front matter — 24 pages

1. Title, institutional metadata and thesis declaration — 2 pages.
2. Résumé français — 4 pages.
3. English abstract — 4 pages.
4. Nomenclature and symbol table — 6 pages.
5. Contribution map and reading guide — 4 pages.
6. Reproducibility/evidence legend — 4 pages.

# Part I — Problem, prior art and foundations — 48 pages

## Chapter 1 — Research problem and falsifiable scope — 12 pages

- coordination complexity across many repositories;
- failure modes of manual all-to-all coupling;
- distinction between software scale and scientific scale;
- central hypotheses and null hypotheses;
- scope boundaries and evaluation criteria.

## Chapter 2 — Prior art in software ecosystems — 12 pages

Compare against:

- monorepos and polyrepos;
- package/dependency managers;
- service registries;
- workflow DAG systems;
- build graphs;
- microservices/service meshes;
- component/plugin systems;
- federated code ecosystems.

## Chapter 3 — Prior art in knowledge and scientific systems — 12 pages

Compare against:

- knowledge graphs;
- provenance graphs;
- workflow/provenance standards;
- scientific CI/reproducibility systems;
- theorem/proof artifact systems;
- evidence graphs;
- multi-agent research orchestration.

## Chapter 4 — Mathematical foundations — 12 pages

Formal foundations for:

- graphs/hypergraphs;
- typed graphs;
- category-inspired composition where justified;
- algebraic interfaces;
- state-transition systems;
- semantics and contracts;
- uncertainty/provenance objects.

# Part II — Formal Mycelial Systems Calculus — 84 pages

Six chapters × 14 pages.

## Chapter 5 — RepoCell and CapabilityCell

Define the shift from repository identity to semantic capability units.

Formal candidate:

```text
C_i = (I,O,T,P,E,U,R,M)
```

with inputs, outputs, transformation, preconditions, evidence, uncertainty, resources and memory.

## Chapter 6 — Capability IR

Define semantic input/output contracts, versions, units/types, evidence requirements and provider substitution.

Study:

```text
Code ≠ Capability
```

and conditions for multiple implementations to realize one semantic capability.

## Chapter 7 — Executable hypergraphs and HGFM

Separate:

```text
Hyperedge as relation
```

from:

```text
Hyperedge as executable program
```

Formalize nested/multiscale structure and the fractal invariance hypothesis.

## Chapter 8 — Repo Algebra

Study operators such as:

```text
A ⊕ B
A ⊗ B
A ∘ B
A ∩ B
A \ B
A ▷ B
A ⇒ B
A★
```

Each operator requires a semantic contract and algebraic properties must be proved or explicitly left as conjectural.

## Chapter 9 — Capability space and routing geometry

Represent a capability by coordinates such as domain, semantics, cost, latency, accuracy, risk, evidence, uncertainty, reuse and maturity.

Turn routing into constrained trajectory optimization.

## Chapter 10 — Local and global invariants

Distinguish:

```text
Truth_local
Truth_global
```

Formalize ecosystem invariants such as provider existence, claim evidence, API versioning, semantic compatibility and cycle constraints.

# Part III — Architecture and Compilers — 84 pages

Six chapters × 14 pages.

## Chapter 11 — Tristan Repo Protocol and Repository ISA

Formalize core objects:

```text
Intent
Capability
WorkUnit
Artifact
Claim
Evidence
Uncertainty
Event
Memory
Action
```

and executable instructions such as DISCOVER, ROUTE, FETCH, TRANSFORM, COMPARE, BENCH, VERIFY, FALSIFY, MERGE, SPLIT, ROLLBACK, LEARN and SPAWN.

## Chapter 12 — Intent-to-RepoGraph compiler

Study compilation:

```text
NaturalLanguage Intent
→ constrained capability graph
→ provider resolution
→ executable HGFM
```

Include ambiguity handling, authority constraints and evidence requirements.

## Chapter 13 — Repo Compiler and Meta-Repo Compiler

Study:

```text
ArchitectureExpression → ExecutableGitHubSystem
ProblemFamily → SystemGenerator
```

with explicit limits on recursion and generation authority.

## Chapter 14 — Theory-to-Repo compiler

Map theory to:

- claims;
- assumptions;
- formal objects;
- simulations;
- required datasets;
- benchmarks;
- counterexamples;
- tests;
- capabilities.

## Chapter 15 — Repo-to-Theory compiler

From code/tests/docs/benchmarks infer candidate implicit assumptions and semantic claims.

The inference is explicitly fallible and audited.

## Chapter 16 — Bidirectional semantic-difference compiler

Study:

```text
Theory ⇄ ExecutableSystem
Δ = Theory − Implementation
```

Define semantic mismatch categories and falsification tests.

# Part IV — Evidence, Trust, OAK and UNC² — 72 pages

Six chapters × 12 pages.

## Chapter 17 — Proof-carrying repositories

Define claims, evidence passports, limitations, provenance and trust boundaries.

## Chapter 18 — Semantic CI

Check meaning rather than syntax alone:

- units;
- semantic types;
- invariants;
- schemas;
- cross-repo contract compatibility.

## Chapter 19 — Scientific CI

Require baselines, controls, provenance, statistics, uncertainty, seeds and counter-hypotheses.

## Chapter 20 — OAK architecture

Formalize PASS/HOLD/FAIL gates and distinguish software validation from scientific validation.

## Chapter 21 — UNC² propagation

Track uncertainty and meta-uncertainty across multi-stage transformations.

## Chapter 22 — Trust graph and evidence gradients

Study capability-specific trust, evidence gradients, confidence debt and how proof strength changes across compositions.

# Part V — Learning, Evolution and Self-Hosting — 60 pages

Five chapters × 12 pages.

## Chapter 23 — Lifecycle calculus

Formalize software analogues of:

- embryogenesis;
- specialization;
- mitosis;
- fusion;
- dormancy;
- absorption/apoptosis.

## Chapter 24 — Negative knowledge and M+/M−/M?

Study propagation of failed strategies, counterexamples, rejected architectures and uncertain hypotheses.

## Chapter 25 — Synergy, GO Gradient and Repo Hessian

Study marginal verified value and pairwise interaction terms for capability investment.

## Chapter 26 — Causal credit assignment

Separate historical association from causal improvement using baselines, counterfactuals and intervention-like benchmark designs.

## Chapter 27 — Self-hosting and fixed points

Study candidate condition:

```text
Compiler(G*) ≈ G*
```

as a reproducibility/closure criterion, never as a claim of unlimited intelligence.

# Part VI — Experiments and Case Studies — 80 pages

Five chapters × 16 pages.

## Chapter 28 — Coordination scaling benchmark

Compare manual all-to-all repository coupling with registry/capability routing across increasing N.

Measure:

- number of explicit relationships;
- configuration effort;
- failure propagation;
- discovery latency;
- reuse ratio;
- maintenance overhead.

## Chapter 29 — Capability substitution benchmark

Create multiple providers for the same Capability IR and test routing by task class, accuracy, cost and latency.

## Chapter 30 — Theory↔code divergence experiment

Inject controlled semantic mismatches and compare detection by:

```text
ordinary tests
Semantic CI
Scientific CI
OAK
```

Measure detection rate, false positives, false negatives and cost.

## Chapter 31 — Reuse-first versus generate-first experiment

Compare:

```text
SEARCH → REUSE → ADAPT → GENERATE
```

against generate-first development.

Measure duplication, integration cost, regression rate, code volume and verified reusable capability yield.

## Chapter 32 — Empirical Tristan GitHub case study

Use the actual authorized GitHub corpus to construct a temporal capability/evidence graph.

Possible analyses:

- capability density;
- duplicated semantic implementations;
- PR-to-capability evolution;
- negative-memory reuse;
- cross-repo reuse;
- global versus local test states;
- bottleneck capabilities;
- high-synergy intersections.

Internal repository history remains internal empirical evidence, not external scientific validation.

# Part VII — Synthesis and Conclusion — 24 pages

## Chapter 33 — Synthesis of validated and falsified contributions — 12 pages

Separate:

```text
validated
partially supported
falsified
unresolved
future work
```

## Chapter 34 — Generalization and research frontier — 12 pages

Discuss boundaries toward:

- distributed scientific operating systems;
- executable epistemology;
- capability markets;
- formal verification;
- large-scale agent systems;
- cross-domain research compilers.

No generalization may outrun measured evidence.

# Bibliography — 24 pages

Target a real research bibliography, not a page quota. The 24-page allocation is provisional and must adapt to the actual source corpus while the global page controller preserves 512 pages through substantive content rebalancing.

# Appendices — 12 pages

Prioritize dense reproducibility material:

1. notation and schemas;
2. benchmark configurations;
3. claim/evidence table excerpts;
4. formal proof details that would interrupt the main text;
5. exact build and environment description;
6. GitHub provenance/hashing conventions.

# Required research artifacts

The profile expects:

```text
thesis_contract.json
corpus_manifest.jsonl
claims_ledger.jsonl
traceability_matrix.jsonl
novelty_matrix.csv
experiment_manifest.jsonl
benchmark_manifest.jsonl
oak_report.json
M_PLUS.jsonl
M_MINUS.jsonl
M_UNKNOWN.jsonl
page_count_receipt.json
```

# Page controller rule

After every full LaTeX build:

```text
delta = 512 − actual_pages
```

Expansion priority:

1. unsupported major claim needing literature/evidence;
2. formal object lacking derivation or counterexample;
3. benchmark lacking baseline/ablation;
4. uncertainty/threat-to-validity gap;
5. reproducibility gap;
6. useful appendix material.

Compression priority:

1. duplicated exposition;
2. redundant definitions;
3. low-value narrative;
4. repeated background;
5. oversized tables/figures with weak information density.

Blank-page padding and artificial spacing are forbidden.

# Final OAK acceptance

The thesis is a promotion candidate only if:

- the LaTeX build succeeds reproducibly;
- the actual PDF page count is 512;
- all major claims have evidence or explicit HOLD status;
- novelty language has prior-art support;
- theory↔code mappings are traceable;
- empirical claims have real benchmark/measurement provenance;
- negative evidence is preserved;
- uncertainty and limitations are visible;
- bibliography and cross-references resolve;
- abstract and conclusion do not exceed the strongest supported claim status.
