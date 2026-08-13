# Ω-PR-RETRIEVAL-ARENA-T — v0.2 frozen baseline

## Purpose

Measure whether historical GitHub memory can recover prior PR ancestry with a bounded context budget, while keeping the target and all future PRs outside the retriever.

The arena is an experimental measurement layer for #450. It does not promote a ranking policy to semantic truth or write authority.

## Frozen policies

The v0.2 evaluation keeps the v0.1 ranking rules unchanged:

- `lexical_jaccard`: current title/body/file token similarity baseline;
- `recency`: deterministic creation-order prior;
- `graph_centrality`: prior-lineage graph degree signal;
- `hybrid_rrf`: reciprocal-rank fusion over lexical, PR-Genome, recency and graph-centrality rankings.

No ranking weights were changed after observing the first 3-target v0.1 result.

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

## M- frontier

Known misses should remain visible instead of being silently optimized away on the same benchmark:

```text
#323 -> #313    missed
#347 -> #338    missed by hybrid at k=8
#447 -> #414,#417,#443
         retrieved: #443
         missed:    #414,#417
```

These failures form a tuning set only after a separate future validation set exists.

## Promotion protocol

The current policy remains `PROBATIONARY`.

Do **not** tune the frozen ranker on the v0.2 baseline cases. Future eligible PRs created after this baseline should become untouched prospective cases. Promotion requires at minimum:

- continued zero target/future leakage;
- enough new prospective targets to estimate stability;
- exact implementation/source inspection before any reuse action;
- no material prospective collapse in recall/MRR;
- multi-repository or external replication when suitable history exists.

## OAK boundaries

```text
ARENA_WINNER != GENERALIZATION
RETROSPECTIVE_HOLDOUT != PROSPECTIVE_VALIDATION
SAME_REPOSITORY_HISTORY != EXTERNAL_REPLICATION
LINEAGE_RECALL != ALL_USEFUL_REUSE
STACK_BASE_REF != SEMANTIC_DEPENDENCY_PROOF
RECENCY_OR_CENTRALITY != CAUSAL_RELEVANCE
PR_GENOME_SIMILARITY != IMPLEMENTATION_COMPATIBILITY
CI_PASS != ENGINEERING_SAVINGS
```

The practical use today is therefore narrow but valuable:

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
