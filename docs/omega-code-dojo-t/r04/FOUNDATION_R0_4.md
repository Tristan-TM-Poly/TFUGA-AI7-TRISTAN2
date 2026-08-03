# Ω-CODE-DOJO-T∞ R0.4 — Problem Resolution Factory

R0.4 converts the extensible R0.2 frontier and R0.3 learning intelligence into a finite, reproducible problem-resolution loop.

## Objective

Maximize verified solved fixtures per unit cost without confusing finite synthetic success with general correctness, Codewars performance, neural training, formal proof, or resolution of public open problems.

## Current portfolio

The seed portfolio contains 17 original synthetic algorithmic families:

- arrays: sum, even count, two-sum, maximum subarray;
- strings: balanced parentheses and edit distance;
- number theory: GCD and prime counting;
- graphs: shortest path, connected components, DAG detection;
- intervals and search;
- dynamic programming: LIS, coin change, grid path;
- optimization: 0/1 knapsack.

Every family has two initial strategies:

1. a plausible but assumption-fragile heuristic;
2. an exact fixture solver used as fallback.

Failures of the heuristic are preserved as counterexamples. A fixture is marked solved only after an independent family oracle agrees with the candidate output.

## Logical versus materialized scale

The initial logical address space is:

```text
17 families × 2^32 deterministic seeds × 32 difficulty bands
= 2,336,462,209,024 addressable synthetic problems
```

The benchmark materializes 4,096 problems. This does not mean trillions of problems were executed or solved.

## Resolution loop

```text
portfolio cell
→ original synthetic problem
→ fragile strategy
→ independent oracle
→ counterexample on failure
→ exact fallback
→ fixture receipt
→ family metrics
→ best-learning analysis
→ next adversarial distribution
```

## OAK boundary

`SOLVED_FIXTURE` means one materialized original synthetic instance matched its oracle. It does not establish:

- general algorithm correctness;
- optimality;
- human mastery;
- neural-model learning;
- Codewars affiliation or rank;
- resolution of an externally published or open mathematical problem.

R0.5 should introduce subprocess isolation, real multi-language implementations, property-based fuzzing, shrinking, differential oracles, time/memory budgets and a persistent unresolved-problem queue.
