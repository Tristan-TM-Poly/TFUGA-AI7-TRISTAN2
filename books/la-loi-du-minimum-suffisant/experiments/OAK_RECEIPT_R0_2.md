# OAK Receipt — Minimum Sufficient Basis R0.2

**Status:** `LOCAL_REPLAY_PASS / EXACT_HEAD_CI_PASS / MERGED`

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

## Observed qualification

- local Python replay: `6/6` unit tests PASS;
- exact-head GitHub `Ω Actions ΔCI Audit R0.3`: `SUCCESS` on `a10a70eeb83399b90b596c77cd32eeb32d91b41a`;
- qualified branch remained current with canonical `main` before promotion;
- PR #486 merged as `59340dff46cf9517930b7150ab97276abfea5028`.

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
- exact-head CI is repository evidence, not independent scientific replication;
- independent replay remains a separate promotion gate.

## Next discriminating experiments

1. compare exact result to greedy set-cover baselines on finite fixtures;
2. add weighted risk/debt dimensions and Pareto output before scalarization;
3. implement a cross-scale fixture where local ablation is misleading globally;
4. benchmark regenerate-vs-persist total cost on a real software artefact.
