---
name: github-pr-llmt
description: Analyze one or all open PRs through cumulative history, exact inspection, reuse, solutions, optimization and OAK.
---

# GitHub PR LLMT

Use this skill for work on an existing or proposed GitHub pull request.

## Governing sequence

```text
portfolio
→ target PR packet
→ prior-history ranking
→ explicit later descendants
→ progressive exact inspection
→ reuse/compose/extend decision
→ competing solutions/optimizations
→ tests + CI evidence
→ OAK
→ residual change plan
→ ReuseOutcomeReceipt / M+ / M- / M?
```

## Required behavior

1. Load the canonical `GitHubMemoryIndex`; never create a parallel PR memory database.
2. Compile `omega_capability_os_t.github_pr_llmt portfolio` for repository-wide work, or `packet` for one target PR.
3. Treat `historical_retrieval.candidates` as a **probationary inspection queue** produced by frozen `hybrid_rrf`. The policy has retrospective cross-repository replication inside the Tristan ecosystem, not prospective or independent external validation.
4. Keep `known_later_descendants` separate from ranked ancestors. A later descendant can reveal reuse/supersession evidence but the validated historical ranker does not justify ranking future descendants from an earlier target.
5. Before proposing new implementation, progressively inspect only the highest-value candidates using the existing #447 Zoom/AST machinery: exact head SHA → changed files → source symbols → tests/CI/reviews → exact implementation.
6. Search M- before selecting a solution. A past failure is evidence against repeating the same context, not a universal refutation.
7. Prefer `REUSE`, then `COMPOSE`, then `EXTEND`; `CREATE` only the verified residual.
8. When optimization matters, generate competing candidates and let tests/benchmarks decide. Do not promote static scores, LLM preference or agent votes over measured evidence.
9. Produce a bounded work result containing at minimum: `intent_summary`, `reuse_plan`, `problem_findings`, `solution_candidates`, `optimization_candidates`, `tests_to_run`, `oak_decision`, `residual_change_plan`.
10. Record exact provenance to PR, head SHA, file/symbol/test evidence and uncertainty.
11. Packet generation and analysis grant **no write, review, merge, publication or deployment authority**. Those actions remain separately authorized.

## Hard boundaries

```text
RANKED_CANDIDATE != REUSABLE_IMPLEMENTATION
PR_SIMILARITY != SEMANTIC_EQUIVALENCE
AST_SYMBOL != BEHAVIORAL_EQUIVALENCE
DECLARED_LINEAGE != CAUSAL_DEPENDENCY_PROOF
LATER_DESCENDANT != AUTOMATIC_SUPERSESSION
MERGED != M+
CLOSED != M-
CI_GREEN != EXTERNAL_TRUTH
MULTIPLE_LLMT_VIEWS != INDEPENDENT_EVIDENCE
PACKET_GENERATION != GITHUB_WRITE_AUTHORITY
```

The goal is not more PR commentary. The goal is to make each new PR reuse more verified historical work, introduce less duplicate code, carry stronger evidence, and leave better memory for the next PR.
