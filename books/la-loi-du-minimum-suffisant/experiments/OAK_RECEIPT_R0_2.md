# OAK Receipt — Minimum Sufficient Basis R0.2

**Status:** `LOCAL_REPLAY_PASS / REPOSITORY_CI_PENDING`

## Claim under test

A bounded finite instance of the Minimal Generating Basis problem can be solved exactly by exhaustive subset search, with deterministic selection by:

1. minimum persistent component count;
2. minimum summed persistence cost;
3. lexical tie-break.

This receipt does **not** claim a scalable optimal solver for the general set-cover family.

## Artefacts

- `minimum_sufficient_basis.py`
- `test_minimum_sufficient_basis.py`
- `../CHAPTER_GRAPH.json`

## Replay

```bash
cd books/la-loi-du-minimum-suffisant/experiments
python -m unittest -v test_minimum_sufficient_basis.py
python minimum_sufficient_basis.py
```

## Observed local replay

`6/6` unit tests passed on Python 3 during the authoring session.

Covered cases:

- minimum cardinality before persistence-cost tie-break;
- lower-cost tie-break at equal cardinality;
- local necessity exposed by ablation;
- redundant components produce zero local required-capability loss;
- unreachable requirements fail closed;
- oversized exact-search instances are refused rather than silently approximated.

## OAK limits

- local ablation is not global uselessness;
- declared capability sets are only as valid as their measurement/model;
- no cross-scale causal validity is inferred from this toy solver;
- exhaustive search is combinatorial and capped at 20 components by default;
- the chapter graph is a design dependency graph, not empirical proof of the theory;
- repository CI and independent replay remain separate promotion gates.

## Next discriminating experiments

1. compare exact result to greedy set-cover baselines on finite fixtures;
2. add weighted risk/debt dimensions and Pareto output before scalarization;
3. implement a cross-scale fixture where local ablation is misleading globally;
4. benchmark regenerate-vs-persist total cost on a real software artefact.
