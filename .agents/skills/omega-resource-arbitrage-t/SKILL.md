---
name: omega-resource-arbitrage-t
description: Choose among observation, compute, reuse, persistent storage, regeneration, waiting and external action by explicit multi-resource tradeoffs. Use for store-vs-recompute, measure-vs-simulate, precompute-vs-JIT, adaptive fidelity, or representation/solver arbitration.
---

# Ω Resource Arbitrage T

## Core rule

Do not minimize one resource while hiding cost in another. Use an explicit vector for action, compute, persistent memory, observation, human attention, time, persistent complexity, risk and irreversibility.

## Workflow

1. State the decision deadline and quality/evidence contract.
2. Generate candidates across `OBSERVE`, `COMPUTE`, `REUSE`, `STORE`, `REGENERATE`, `WAIT`, `NO_ACTION`, and only when authorized `ACT`.
3. Include conversion overhead: transform cost, cache maintenance, measurement cost, verification cost and recomputation.
4. Compare Pareto frontiers before weighting.
5. Prefer reversible information-gathering when it can remove a costly or irreversible action.
6. Prefer lifetime/amortized cost over local cost when horizon evidence exists.
7. Preserve uncertainty where prices/weights are not justified.

## Anti-rules

- Cheaper compute does not justify weaker evidence.
- Less memory does not justify losing provenance.
- Faster output does not authorize external action.
- A representation benchmark is not a universal complexity theorem.
