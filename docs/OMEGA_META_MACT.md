# Ω-META-MACT-MORPHOGENESIS-T∞Ω

## Status

Engineering research kernel. This implementation does not establish a new law of physics, universal optimality theorem, scientific validity, or authority to act.

## Thesis

For a verified target state, search the finite candidate set for the least irreducible transformation on a multi-resource Pareto frontier. The target contract is explicit: a zero-cost `NO_ACTION` candidate is invalid when it does not satisfy the required semantic effect.

The resource vector is `(action, compute, memory_persistent, observation, human_attention, time, persistent_complexity, risk, irreversibility)`.

## Selection contract

1. Enumerate a bounded candidate set.
2. Require `NO_ACTION`, `WAIT`, `REUSE`.
3. Attach target semantics, evidence, authority and rollback.
4. Run non-compensatory hard gates **before** optimization.
5. Invalid/HOLD candidates cannot Pareto-dominate valid candidates.
6. Compute the Pareto front only among eligible candidates.
7. Rank eligible non-dominated candidates with declared weights and future-work leverage.
8. Emit a proof-carrying receipt.
9. Never execute external actions from this planning kernel.

This ordering was added after adversarial review exposed two failure modes: minimizing without a semantic target selected `NO_ACTION` even when the goal was unmet, and Pareto filtering before hard gates allowed an invalid low-cost candidate to erase valid alternatives.

## Meta-stop

Optimization itself has a cost. `meta_stop_gate` allows a new optimization/meta layer only when expected savings exceed optimization cost + complexity debt + risk debt + margin. This is an engineering gate, not a universal optimality proof.

## Regenerative memory

Memory decisions are `KEEP`, `COMPRESS`, `REGENERATE_ON_DEMAND`, `ARCHIVE`, `HOLD_DELETE`. Evidence/provenance and non-reconstructible state are fail-closed. There is no automatic destructive delete.

## OAKBench-MACT v1 toy benchmark

The deterministic toy court includes:

- reuse vs recompute at matched declared semantics;
- verified regeneration/reuse vs persistent storage at matched declared semantics.

Local pre-publication results after the adversarial fixes: **14/14 focused tests PASS**, benchmark **2/2 cases PASS**. These are software-fixture results only.

## Falsifiable frontier

The engineering hypothesis survives only if explicit baselines show lower compute, persistent memory, attention or persistent complexity at matched target/evidence quality without increasing unsupported claims, risk or irreversibility. Future work should add real representation-arbitrage, adaptive-fidelity, verification-compression and meta-stop benchmarks.

## Permanent boundaries

`Minimum != Brittle`

`Generated != Verified`

`Simulation != Reality`

`Capability != Authority`

`Pareto-better in benchmark != universally optimal`

`Reconstructible in fixture != safe to delete in reality`

`Compute reduction != truth improvement`

`Compression != explanation`

`Automation != permission`
