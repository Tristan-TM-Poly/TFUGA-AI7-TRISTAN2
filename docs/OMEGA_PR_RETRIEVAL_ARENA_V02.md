# Ω-PR-RETRIEVAL-ARENA-T — v0.2 frozen baseline + cross-repository replication

## Purpose

Measure whether historical GitHub memory can recover prior PR ancestry with a bounded context budget, while keeping the target and all future PRs outside the retriever.

The arena is an experimental measurement layer for #450. It does not promote a ranking policy to semantic truth or write authority.

## Frozen policies

The v0.2 evaluation keeps the v0.1 ranking rules unchanged:

- `lexical_jaccard`: current title/body/file token similarity baseline;
- `recency`: deterministic creation-order prior;
- `graph_centrality`: prior-lineage graph degree signal;
- `hybrid_rrf`: reciprocal-rank fusion over lexical, PR-Genome, recency and graph-centrality rankings.

No ranking weights were changed after observing the first 3-target v0.1 result, the 16-target v0.2 result, or either cross-repository replication.

## Gold labels

Gold ancestry is assembled only after ranking from two bounded sources:

1. explicit historical body directives such as `reuses`, `extends`, `derived_from`, `supersedes`, `replaces`;
2. a unique structural stack parent when the target PR base branch exactly equals a lower-numbered prior PR head branch.

Default-like bases (`main`, `master`, `develop`, `development`, `trunk`) are excluded and ambiguous reused branch names are rejected.

The target body and target base branch are **gold-only fields**. They are never passed into the rankers.

## Exact-head v0.2 result

Source head: `ea7ffe1a178ce5cabb197689a61bb039678903a0`

Workflow run: `31676766222`

Artifact digest: `sha256:87f3c9718b1970dd75fd3a1981d81a129c9a0e07bc05cbb2a7fa0b2ce9f64c41`

Corpus:

```text
350 PRs
16 eligible historical targets
21 unique gold ancestry refs
8 declared-body labels
16 structural stack labels
0 ambiguous structural labels
```

Top-k = 8:

| strategy | hits | micro Recall@8 | macro Recall@8 | MRR | leakage |
|---|---:|---:|---:|---:|---:|
| lexical_jaccard | 0 | 0.000000 | 0.000000 | 0.000000 | 0 |
| recency | 15 | 0.714286 | 0.781250 | 0.400521 | 0 |
| graph_centrality | 17 | 0.809524 | 0.833333 | 0.436979 | 0 |
| hybrid_rrf | 17 | **0.809524** | **0.833333** | **0.564583** | 0 |

`hybrid_rrf` wins the v0.2 arena because it matches graph centrality on recall while ranking relevant ancestors earlier on average.

## Temporal stress test

The same frozen ranker is evaluated on an ordered 60/40 retrospective split.

```text
early: 9 targets / 9 gold refs
hybrid Recall@8 = 0.888889
hybrid MRR      = 0.540741

late holdout proxy: 7 targets / 12 gold refs
hybrid Recall@8 = 0.750000
hybrid MRR      = 0.595238
```

The late cohort is a retrospective holdout proxy, not a pristine prospective benchmark.

## Cross-repository replication — frozen ranker

The ranker was then executed unchanged against two additional historical repositories using `state=all`, `--without-files`, and the same top-k=8 court. These tests were not used to alter weights between runs.

Workflow run: `31677316267`

### `Tristan-TM-Poly/Tristan_Tardif-Morency_TFUG`

```text
23 eligible targets
23 structural gold refs
lexical Recall@8 = 0.434783
lexical MRR      = 0.229710
hybrid Recall@8  = 1.000000
hybrid MRR       = 0.740580
leakage           = 0
status            = REPLICATED
```

Arena fingerprint: `86ecf7ff3d32bf291ce4aaef10db55f3ba9d60c3c7fdf21b249439c995bc1712`

Artifact ID: `9172037637`

Artifact digest: `sha256:632dc9444be49e320be2e62e76290824569bdd7610f3f5bae51c01d3280ae5ef`

### `Tristan-TM-Poly/TTM-TFUGA-AI7-TRISTAN2`

```text
135 eligible targets
135 structural gold refs
lexical Recall@8 = 0.259259
lexical MRR      = 0.091455
hybrid Recall@8  = 0.896296
hybrid MRR       = 0.580661
leakage           = 0
status            = REPLICATED
```

Arena fingerprint: `a988b2e5ed518d9b6351e1a6a0f29a63aa2c0ee3af542496499bf3ebfaf70536`

Artifact ID: `9172056122`

Artifact digest: `sha256:50cdc8ea58944f2389f5e254d722f9060ad670a930dcf50e3b8de3409ab51502`

### Descriptive pooled view

Across the two replication repositories there are 158 eligible targets and 158 structural gold refs.

```text
lexical hits        = 45 / 158
hybrid hits         = 144 / 158
lexical Recall@8    = 0.284810
hybrid Recall@8     = 0.911392
target-weighted lexical MRR = 0.111581
target-weighted hybrid MRR  = 0.603940
leakage             = 0
```

This pooled summary is descriptive only. The repositories are related parts of the same Tristan ecosystem and all cross-repository gold labels in this suite are structural stack-base labels. They are not independent random samples.

The immutable replication receipt is stored in `benchmarks/omega_pr_retrieval_cross_repo_replication_v01.json`.

## M- frontier

Known misses from the original #450 v0.2 baseline remain visible instead of being silently optimized away on the same benchmark:

```text
#323 -> #313    missed
#347 -> #338    missed by hybrid at k=8
#447 -> #414,#417,#443
         retrieved: #443
         missed:    #414,#417
```

These failures form a tuning set only after a separate future validation set exists.

## Evidence state after replication

The frozen ranker has now passed three distinct retrospective repository courts:

```text
#450 historical baseline                         -> gain observed
Tristan_Tardif-Morency_TFUG cross-repo court    -> gain replicated
TTM-TFUGA-AI7-TRISTAN2 cross-repo court         -> gain replicated
```

This upgrades the evidence from a single-repository retrospective result to **cross-repository retrospective replication within the same ecosystem**.

It does **not** establish:

```text
prospective validation
independent external replication
semantic implementation compatibility
causal engineering savings
optimality of hybrid_rrf
```

## Promotion protocol

The current policy remains `PROBATIONARY`.

Do **not** tune the frozen ranker on the v0.2 baseline or the two replication repositories. Future eligible PRs created after the frozen baseline should become untouched prospective cases. Promotion requires at minimum:

- continued zero target/future leakage;
- enough new prospective targets to estimate stability;
- exact implementation/source inspection before any reuse action;
- no material prospective collapse in recall/MRR;
- measured downstream engineering outcomes such as accepted reuse, LOC avoided, CI attempts, regressions and maintenance;
- replication outside the same project ecosystem when a comparable corpus is available.

## OAK boundaries

```text
ARENA_WINNER != GENERALIZATION
RETROSPECTIVE_HOLDOUT != PROSPECTIVE_VALIDATION
CROSS_REPO_WITHIN_ONE_ECOSYSTEM != INDEPENDENT_EXTERNAL_REPLICATION
LINEAGE_RECALL != ALL_USEFUL_REUSE
STACK_BASE_REF != SEMANTIC_DEPENDENCY_PROOF
RECENCY_OR_CENTRALITY != CAUSAL_RELEVANCE
PR_GENOME_SIMILARITY != IMPLEMENTATION_COMPATIBILITY
CI_PASS != ENGINEERING_SAVINGS
```

The practical use today is therefore:

```text
new PR intent
-> cumulative memory
-> probationary retrieval ranking
-> exact candidate inspection
-> reuse/composition/extension decision
-> tests/OAK
-> ReuseOutcomeReceipt
-> M+/M-/M?
```
