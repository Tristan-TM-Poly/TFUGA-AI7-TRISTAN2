# Ω-PROBLEM-ATLAS-T∞ R0.3 MAX — architecture analysis

## Executive result

The compact R0.3 seed contains 72 conservative problem families over 24 fronts.
The MAX engine expands each problem into 12 falsifiable research targets and
then crosses each target with 8 attack modes:

```text
72 problems × 12 targets/problem = 864 research targets
864 targets × 8 attack modes = 6,912 evidence work cells
```

This is a research decomposition, not a claim that the repository contains 864
independently sourced open conjectures.  The distinction is deliberate:
external problem identity and current status require fresh primary-source
verification, while generated targets are internal work packages.

## Problems found in the compact implementation

### 1. Opaque priority noise

The compact engine used deterministic SHA-256 fractions to vary fertility,
transferability, testability, formalizability, uncertainty and false-progress
risk.  Although reproducible, those values had no evidential interpretation.
They could create a false appearance of quantitative knowledge.

**MAX correction:** priorities are computed from declared target profiles,
attack-mode profiles, evidence readiness and explicit risk penalties.  Every
cell records `scoring_basis: transparent_profile_v1`.

The score is a routing heuristic, never a probability that a method or theorem
is correct.

### 2. Insufficient decomposition depth

Eight attack modes directly attached to each problem produced only 576 cells
and mixed several different objects: statement recovery, restricted theorems,
known-case reconstruction, computation and formalization.

**MAX correction:** insert a typed target layer with 12 target kinds:

1. canonical statement;
2. literature/status audit;
3. equivalent form;
4. known-case reconstruction;
5. toy model;
6. finite case;
7. weakened form;
8. conditional theorem;
9. barrier/no-go test;
10. counterexample frontier;
11. computational certificate;
12. formalization target.

Every target declares required evidence and an explicit falsifier.

### 3. Portfolio concentration

A global sort can select many cells from one front or several nearly identical
cells from one problem.

**MAX correction:** balanced deterministic selection rotates across all 24
fronts and enforces per-problem and per-target limits.  A 24-cell primary
portfolio therefore covers all 24 fronts before allocating additional depth.

### 4. Weak integrity audit

The compact audit checked row counts and forbidden claim flags, but did not
prove that an artifact was unchanged after generation.

**MAX correction:** the build emits a manifest with SHA-256, byte length and row
count for every artifact.  The MAX audit recomputes these receipts, checks
unique identifiers, referential integrity, method references, portfolio
budgets and bucket overlap.

### 5. Shallow transfer graph

The compact hypergraph only represented `problem + attack mode -> cell`.

**MAX correction:** the graph now includes:

```text
problem -> research target
typed canonical statement -> every derived target
target + attack mode + method families -> evidence work cell
```

The method nodes connect domains without asserting invalid mathematical
implications.  A shared method means a possible transfer route, not proof that
results transfer.

### 6. Unicode title damage

ASCII-only title normalization could turn names such as `Erdős` into broken
keys such as `erd s`.

**MAX correction:** Unicode NFKC normalization retains meaningful letters and
uses alphanumeric token boundaries.

## MAX artifact contract

```text
sources.jsonl          source policy and refresh requirements
problems.jsonl         externally anchored problem-family records
research_targets.jsonl internal decompositions with evidence/falsifiers
research_cells.jsonl   executable research work cells
methods.jsonl          reusable mathematical/computational method nodes
hyperedges.jsonl       problem-target-method-cell relations
portfolio.json         balanced active routing
manifest.json          SHA-256 and size receipts
report.json            OAK status and counts
```

## Default active portfolio

| Layer | Budget | Purpose |
|---|---:|---|
| Primary | 24 | one high-value cell per mathematical front |
| Secondary | 72 | additional depth with at most two cells per problem |
| Experiments | 256 | broader finite numerical, formal and adversarial work |

These are finite scheduling budgets.  They are not a permanent atlas ceiling.
The field `permanent_total_cap` remains null.

## OAK interpretation

The MAX engine may certify only that:

- files conform to the software contracts tested by CI;
- materialization is deterministic;
- identifiers and references are internally consistent;
- artifacts match their SHA-256 receipts;
- no seed, target or work cell claims a solution or completed proof;
- the portfolio covers the declared fronts under the configured budgets.

It does **not** certify:

- that every title remains an open problem today;
- that a generated target is mathematically fertile;
- that a numerical result is a theorem;
- that a formal skeleton is a kernel-checked proof;
- novelty, publication acceptance or prize eligibility;
- Clay Mathematics Institute recognition.

## Scale analysis

The first MAX materialization is intentionally finite:

```text
72 source problem families
864 research targets
6,912 research cells
32 method families
8,568 hyperedges
```

With `P` deduplicated imported problems, the deterministic base expansion is:

```text
research_targets = 12P
research_cells   = 96P
hyperedges       = P + 11P + 96P = 108P
```

Examples:

| Verified imported problem families | Targets | Cells | Hyperedges |
|---:|---:|---:|---:|
| 72 | 864 | 6,912 | 8,568 |
| 256 | 3,072 | 24,576 | 27,648 |
| 1,000 | 12,000 | 96,000 | 108,000 |
| 5,000 | 60,000 | 480,000 | 540,000 |

These numbers measure generated research work packages, not proofs or unique
external conjectures.

## Highest-value next engineering phases

### Phase A — Primary-source adapters

Implement revision-pinned, terms-respecting adapters for official and curated
catalogs.  Each imported record must include source locator, retrieval time,
statement version, license note and a status verification receipt.

### Phase B — Alias and statement deduplication

Add explicit aliases, citation identifiers, statement fingerprints and manual
merge records.  Title similarity alone must never merge two mathematically
different conjectures.

### Phase C — Claim/evidence graph

Attach known theorems, bounds, counterexamples, papers, formal artifacts and
computational receipts to targets.  Separate evidence existence from evidence
support.

### Phase D — Executable campaign runners

Compile selected work cells into isolated jobs for exact arithmetic, SAT/SMT,
interval methods, graph search, symbolic algebra, simulation and proof
assistants.  Every run should produce environment, input, output, hash, error
bounds and M-minus records.

### Phase E — Adaptive evidence routing

Update priorities only from recorded outcomes: reproduction success, valid
counterexample, improved bound, discharged assumption, failed method or
independent review.  Never update a mathematical truth score from model
confidence.

### Phase F — Publication and IP gate

Before public claims, require a dated literature search, novelty audit,
reproducible repository snapshot, complete assumptions, negative results,
independent mathematical review and a decision on open publication, patent,
secret or abandonment.

## Strategic conclusion

The main advantage of a large atlas is not the raw number of attempted
problems.  It is the reusable accumulation of definitions, formal libraries,
counterexample generators, exact arithmetic, numerical certificates,
reduction graphs, failed approaches and transferable lemmas.

The correct growth loop is:

```text
more sourced problems
-> more typed targets
-> more reproducible experiments
-> more evidence and negative memory
-> better routing
-> fewer unsupported claims
-> stronger reusable mathematics
```

R0.3 MAX is therefore a scalable research operating layer, not an automated
open-problem solver and not a theorem factory by declaration.
