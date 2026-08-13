# Default thesis profile — TTM-GitHub-001 / Ω-MYCELIAL-SYSTEMS-CALCULUS-T

## Candidate title

**Calcul mycélien des écosystèmes logiciels et scientifiques distribués : hypergraphes exécutables, représentation intermédiaire des capacités, compilation bidirectionnelle théorie–code et validation épistémique**

English working title:

**A Mycelial Calculus for Distributed Software–Scientific Ecosystems: Executable Hypergraphs, Capability Intermediate Representations, Bidirectional Theory–Code Compilation, and Evidence-Carrying Validation**

This is a candidate title, not a novelty claim.

## Research object

The manuscript studies a GitHub-scale research ecosystem not as a bag of repositories but as a multiscale executable system in which repositories, modules, functions, capabilities, claims, evidence, tests, benchmarks, agents, transformations, and histories are typed objects linked by executable hyperedges.

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

> Can a large, heterogeneous, evolving research-code ecosystem be represented and operated as a typed multiscale hypergraph of capabilities such that composition, reuse, evidence propagation, semantic consistency, and controlled self-improvement become explicit, testable, and scalable properties rather than ad-hoc repository conventions?

## Subquestions

1. What should be the fundamental unit: repository, module, function, or semantic CapabilityCell?
2. Can a Capability IR decouple semantic demand from concrete implementation provider?
3. Which algebraic operators are sufficient to express composition, intersection, adaptation, migration, and closure of research-software systems?
4. How should an executable hyperedge differ formally from an ordinary dependency edge?
5. Can natural-language intent be compiled into an executable repository/capability hypergraph while preserving constraints and evidence requirements?
6. Can theory and implementation be compiled bidirectionally and compared by a semantic-difference operator?
7. How should evidence, uncertainty, negative results, provenance, and trust propagate across repository boundaries?
8. Can local CI success be separated from global scientific/ecosystem validity?
9. Which lifecycle operations—specialization, mitosis, fusion, dormancy, absorption/apoptosis—have useful formal software analogues?
10. Can the ecosystem learn which transformations improve future architecture without confusing historical association with causality?
11. What measurable conditions justify self-hosting and fixed-point claims?
12. Under what workloads does the proposed architecture outperform simpler baselines such as monorepos, static dependency graphs, service registries, package managers, workflow DAGs, and conventional agent orchestration?

## Candidate thesis statement

A plausible thesis statement to test—not assume—is:

> A capability-centered, typed, multiscale executable-hypergraph architecture can reduce coordination friction and increase reusable verified composition in large research-code ecosystems when its semantic contracts, evidence propagation, routing, lifecycle operations, and self-improvement mechanisms are subjected to explicit global invariants, reproducible benchmarks, uncertainty tracking, and falsification gates.

The manuscript must weaken, refine, or reject this statement if experiments do not support it.

## Formal core

### 1. Repository state

Candidate state model:

\[
R_i = (I,C,P,Cl,E,A,T,M,Pol,D,Ev),
\]

where identity, capabilities, ports, claims, evidence, artifacts, tests, memory, policies, dependencies, and events are explicit typed components.

### 2. CapabilityCell

Candidate semantic unit:

\[
C_i=(I,O,T,P,E,U,R,M),
\]

with inputs, outputs, transformation, preconditions, evidence, uncertainty, resources, and memory.

The thesis must specify typing, equality/equivalence, substitution conditions, versioning, and failure semantics.

### 3. Repository hypergraph

Candidate multiscale object:

\[
\mathcal G_{repo}=(V_R,E_H,E_V,E_T),
\]

with repository nodes, composition hyperedges, Venn/intersection structures, and temporal transformation edges.

A stronger formalization should distinguish:

- ordinary graph edge;
- typed dependency;
- hyperedge;
- executable hyperedge;
- temporal transition;
- semantic intersection;
- evidence/trust edge.

### 4. Repository algebra

Candidate operators:

\[
A\oplus B,\quad
A\otimes B,\quad
A\circ B,\quad
A\cap B,\quad
A\setminus B,\quad
A\triangleright B,\quad
A\Rightarrow B,\quad
A^\star.
\]

The manuscript must define domains/codomains and laws rather than relying on notation alone. Associativity, identity elements, closure, commutativity, monotonicity, distributivity, partiality, and failure propagation should be proved, disproved, or explicitly left open for each operator.

### 5. Capability space

Candidate coordinate model:

\[
c_i=(domain,semantics,cost,accuracy,latency,risk,evidence,uncertainty,reuse,maturity).
\]

Intent becomes a target region in capability space, and routing becomes constrained trajectory optimization.

### 6. Global value functional

Candidate GO-MAX-inspired objective:

\[
\mathcal L=\frac{
VerifiedReusableCapabilities\times UsefulCompositions\times Evidence
}{
Duplication+Cost+Coupling+Debt
}.
\]

This must be operationalized into measurable proxies before empirical claims are made.

## Candidate contribution families

All novelty labels remain `HOLD` until literature review.

### C1 — Capability-centered multiscale ontology

Repository-level architecture grounded in semantic capabilities rather than only source-code packaging boundaries.

### C2 — Capability IR

A typed intermediate representation for semantic inputs/outputs, evidence, uncertainty, quality, and provider substitution.

### C3 — Executable hyperedges

Hyperedges treated as executable programs/workflows with participants, transformations, evidence contracts, and learned value.

### C4 — Repo Algebra and compiler stack

An algebra of ecosystem composition plus compilation from intent/architecture expressions to executable repository graphs.

### C5 — Bidirectional Theory ⇄ ExecutableSystem compilation

Theory-to-repository graph generation combined with repository-to-implicit-theory extraction and semantic difference analysis.

### C6 — Proof-/evidence-carrying repositories

Repository passports carrying claims, evidence, limits, uncertainty, provenance, and security/validation status.

### C7 — Semantic and Scientific CI

CI layers that test semantic contracts, units, baselines, provenance, uncertainty, negative controls, and scientific-claim support separately from software correctness.

### C8 — Multiscale lifecycle calculus

Formal software operations inspired by biological metaphors: embryogenesis/incubation, mitosis, fusion, dormancy, absorption/apoptosis, recombination, and horizontal transfer.

### C9 — Negative-knowledge and uncertainty propagation

M− and UNC² propagated through capability chains rather than discarded locally.

### C10 — Controlled self-hosting and meta-evolution

The system analyzes and proposes changes to itself while generation remains distinct from acceptance and global gates remain authoritative.

## Baseline families for literature/experimental comparison

At minimum compare against relevant concepts from:

- monorepo and multi-repo engineering;
- package managers and dependency graphs;
- service registries and service meshes;
- build systems and incremental build graphs;
- workflow DAG engines;
- dataflow systems;
- microservices and interface description languages;
- component models and software product lines;
- knowledge graphs and provenance graphs;
- hypergraph computation;
- intermediate representations and compiler architectures;
- theorem/proof-carrying code where relevant;
- formal methods and contract-based design;
- scientific workflow/reproducibility systems;
- multi-agent orchestration;
- software architecture mining and repository mining;
- causal inference for software-engineering interventions;
- self-adaptive/autonomic software systems.

The thesis must search current scholarship and standards before asserting novelty against any of these families.

# Exact 256-page architecture

The total includes all front matter, bibliography, and appendices.

## Front matter — 12 pages

- title / institutional pages;
- French abstract;
- English abstract;
- contribution map;
- notation and acronyms;
- compact reader guide.

## Part I — Problem, prior art, foundations — 24 pages

### Chapter 1 — Research problem and falsifiable thesis — 8 pages

- motivation from coordination debt;
- research question;
- scope and non-goals;
- falsification criteria;
- contribution status taxonomy.

### Chapter 2 — State of the art and nearest conceptual baselines — 8 pages

- repository architectures;
- distributed systems;
- compiler IRs;
- workflow/agent systems;
- hypergraphs;
- scientific reproducibility;
- formal contracts.

### Chapter 3 — Epistemic and systems methodology — 8 pages

- OAK;
- UNC²;
- M+/M−/M?;
- provenance;
- local vs global truth;
- experimental methodology.

## Part II — Formal Mycelial Systems Calculus — 42 pages

### Chapter 4 — RepoCell and CapabilityCell ontology — 10 pages

- typed state spaces;
- scale hierarchy;
- semantic identity;
- invariants;
- lifecycle state.

### Chapter 5 — Capability IR and substitution semantics — 10 pages

- semantic types;
- provider independence;
- pre/postconditions;
- uncertainty/evidence types;
- version compatibility.

### Chapter 6 — Executable hypergraphs and multiscale HGFM — 11 pages

- static vs dynamic graph;
- executable hyperedge;
- recursive nesting;
- Venn/intersection cells;
- temporal HGFM.

### Chapter 7 — Repo Algebra, capability space, and optimization — 11 pages

- algebraic operators;
- laws/counterexamples;
- capability-space geometry;
- routing objectives;
- GO Gradient/Hessian interpretation.

## Part III — Architecture and compilers — 42 pages

### Chapter 8 — Tristan Repo Protocol and Repository ISA — 10 pages

- Intent, Capability, WorkUnit, Artifact, Claim, Evidence, Uncertainty, Event, Memory, Action;
- instruction semantics;
- failure and rollback.

### Chapter 9 — Intent-to-RepoGraph and Repo Compiler — 10 pages

- planning;
- capability resolution;
- schema adapters;
- dynamic routing;
- execution graphs.

### Chapter 10 — Theory-to-Repo and Repo-to-Theory compilation — 11 pages

- extracting formal requirements from theories;
- mining implicit assumptions from code;
- semantic diff;
- living documentation.

### Chapter 11 — Cross-repository transactions and digital twins — 11 pages

- synchronized transformations;
- virtual PRs;
- impact simulation;
- ecosystem invariants;
- rollback.

## Part IV — Evidence, trust, OAK and UNC² — 36 pages

### Chapter 12 — Proof-/evidence-carrying repositories — 9 pages

- claim passports;
- evidence receipts;
- provenance;
- trust by capability.

### Chapter 13 — Semantic CI and Scientific CI — 9 pages

- semantic types;
- units;
- schema evolution;
- scientific baselines;
- negative controls;
- dataset provenance.

### Chapter 14 — Local truth, global truth, and ecosystem invariants — 9 pages

- composition failures;
- global contract tests;
- invariant catalog;
- Noether-inspired heuristic separated from theorem claims.

### Chapter 15 — Uncertainty, M−, and causal credit — 9 pages

- uncertainty propagation;
- meta-uncertainty;
- negative result dissemination;
- causal vs correlational architecture improvements.

## Part V — Learning, evolution, and self-hosting — 30 pages

### Chapter 16 — Repo lifecycle: embryogenesis, mitosis, fusion, apoptosis — 10 pages

- virtual capability → module → repo;
- split criteria;
- merge/absorption criteria;
- provenance preservation.

### Chapter 17 — Synergy, knowledge pressure, markets, and resource allocation — 10 pages

- synergy miner;
- gap detector;
- knowledge pressure;
- shadow prices;
- research portfolio allocation.

### Chapter 18 — Primitive mining, self-hosting, and fixed points — 10 pages

- repeated programs → new primitives;
- transformation genome;
- self-analysis;
- fixed-point criteria;
- bounded meta-evolution.

## Part VI — Experiments and case studies — 40 pages

### Chapter 19 — Coordination-scaling benchmark — 10 pages

Compare explicit pairwise repo wiring against capability-registry/on-demand routing under controlled synthetic and real-corpus workloads.

Measure at least:

- number of maintained relations;
- discovery latency;
- integration effort;
- failure localization;
- schema-change propagation;
- human review burden.

Do not claim asymptotic improvement without a defined cost model.

### Chapter 20 — Capability substitution and semantic-contract benchmark — 10 pages

Compare multiple providers for the same Capability IR.

Measure:

- substitutability success;
- adapter burden;
- semantic mismatch rate;
- performance/cost tradeoffs;
- trust/evidence routing quality.

### Chapter 21 — Theory–code consistency and Scientific-CI benchmark — 10 pages

Inject controlled semantic drift and evaluate detection by:

- normal software tests;
- semantic contracts;
- scientific CI;
- OAK gates.

Measure false-positive/false-negative behavior.

### Chapter 22 — Tristan GitHub ecosystem case study — 10 pages

Apply the architecture to the actual authorized Tristan repositories.

Report:

- corpus size and provenance;
- capability map;
- duplicate/reuse opportunities;
- M− propagation examples;
- candidate lifecycle transformations;
- limitations caused by incomplete historical metadata or missing benchmarks.

## Part VII — Synthesis and conclusion — 12 pages

### Chapter 23 — General discussion and threats to validity — 7 pages

- external validity;
- construct validity;
- scale limits;
- security/permissions;
- governance;
- architecture-vs-metaphor boundaries;
- open mathematical questions.

### Chapter 24 — Conclusions and research program — 5 pages

- answer central question only to the strength supported by evidence;
- list supported, partial, falsified, and open contributions;
- bounded future work.

## Bibliography — 12 pages

Target high-density, primary/peer-reviewed/standards-oriented references. Exact count should be driven by coverage, not a vanity number.

## Appendices — 6 pages

- key schemas;
- benchmark contract excerpts;
- reproducibility manifest;
- extended theorem/proof details only if not essential to the main argument.

# Page controller rule

The page allocation above is a starting control vector. The final compiled PDF must equal 256 pages. Move pages between chapters as evidence density demands, but preserve:

```text
Total = 256
```

without filler.

# Default evidence priorities

For this thesis profile, search GitHub in roughly this order:

1. capability/intent/work-unit kernels;
2. OAK and uncertainty kernels;
3. HGFM/hypergraph representations;
4. skill foundry and Capability OS;
5. GitHub living factory/repo intelligence work;
6. PR/commit/history artifacts that show architectural evolution;
7. tests and benchmarks;
8. M−/failure registries;
9. theory cards and canonical docs;
10. experiments and case-specific repositories.

# OAK-sensitive language

Prefer:

- “we define” for explicit new notation/constructions;
- “we implement” for code verified in the corpus;
- “we observe” for measured data;
- “we simulate” for simulations;
- “we hypothesize” for unverified causal mechanisms;
- “we conjecture” for mathematical statements without proof;
- “the literature establishes” only with exact supporting references;
- “candidate contribution” until novelty review passes.

Avoid:

- “revolutionary” as an academic evidence category;
- “proved” for tested code;
- “validated experimentally” for synthetic or simulated data;
- “novel” solely because terminology is internally named;
- biological terms as literal claims about software ecosystems unless formally defined.
