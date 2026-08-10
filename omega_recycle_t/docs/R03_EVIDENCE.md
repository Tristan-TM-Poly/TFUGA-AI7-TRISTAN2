# Ω-RECYCLE-T∞ R0.3 — Evidence Contract

R0.3 is a proof-oriented increment. It adds mechanisms that can fail visibly.

## Court A — solver equivalence

For small candidate sets, compare:

1. exhaustive R0.2 oracle;
2. R0.3 branch-and-bound.

Pass condition:

```text
same selected modes AND |score_exact - score_bnb| <= 1e-9
```

A bounded search that does not finish must return `optimality_certified = false`.

## Court B — counterfactual baselines

Every benchmark can compare:

- canonical score policy;
- mass-only recovery;
- value-only recovery;
- canonical policy with preservation and future-cycle terms ablated.

The preservation prior is useful only if it improves an externally chosen objective on real data. The package does not assume this result.

## Court C — uncertainty

`BetaFunctionalPosterior` represents uncertainty in functional probability. Seeded posterior sampling propagates that uncertainty to route winners.

This is not calibration. Posterior parameters must eventually come from inspection or historical evidence.

## Court D — LCA boundary

`inventory_for_route` produces mass and energy inventory flows. It performs no characterization, normalization, weighting or system-expansion logic.

Therefore:

```text
inventory != lifecycle impact result
```

## Court E — provenance

Dataset records can be canonically hashed and associated with source URL, retrieval time and license metadata. Hashing proves byte/record identity, not source truth.

## R0.3 promotion criteria

- unit tests pass on CPython 3.11, 3.12 and 3.13;
- OAKBench is deterministic;
- solver cross-check passes;
- finite search budgets never claim optimality;
- hazardous routes remain simulation-only;
- no LCA superiority language is emitted by the package.
