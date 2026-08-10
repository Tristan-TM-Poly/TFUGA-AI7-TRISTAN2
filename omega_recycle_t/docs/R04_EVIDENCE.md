# Ω-RECYCLE-T∞ R0.4 Evidence Contract

R0.4 is promoted only if all courts remain explicit and reproducible.

## Court A — transport optimality

For the declared finite bipartite supply-demand graph, `min_cost_transport` must maximize transported quantity first and minimize declared unit cost second. The implementation is dependency-free residual min-cost flow using Bellman-Ford shortest augmenting paths.

This is not a claim about arbitrary industrial logistics, multi-commodity routing, stochastic capacity, congestion or dynamic networks.

## Court B — greedy symbiosis regret

The historical greedy matcher remains available as a baseline. R0.4 adds an exact matcher and a regret report.

Canonical counterexample:

```text
A1: 1 unit @ 1.0 -> B1 or B2
A2: 1 unit @ 2.0 -> B1 only
B1 accepts <= 2.0
B2 accepts <= 1.5
```

The greedy ordering takes A1->B1 and strands A2, recovering 1 unit. The exact matcher takes A1->B2 and A2->B1, recovering 2 units. This failure is intentionally preserved in M-.

## Court C — calibration

Functional-state probabilities may only be called calibrated after comparison with observations. R0.4 exposes Brier score, log loss, reliability bins and expected calibration error. A low score on one sample does not establish stationarity, causal validity, fairness or safety.

## Court D — public-data provenance

A caller-supplied delimited snapshot is normalized, canonically hashed and bound to source metadata plus retrieval time. Hash equality means parsed-record identity only.

Source catalog entries are not cached truth. Upstream revisions, definitions, units, licenses and comparability warnings remain part of the evidence graph.

## Court E — LCIA adapter

R0.4 can apply externally supplied characterization factors to inventory flows and reports unmatched flows. It deliberately ships no endorsed factor set. Output remains screening characterization, not certified LCA or proof of environmental superiority.

## Promotion gate

R0.4 may be called D-MVP++ only when:

1. all R0.3 oracle/B&B courts remain green;
2. the greedy counterexample is detected;
3. the transport court returns the 2-unit optimum;
4. public snapshot hashing is reproducible;
5. calibration metrics are deterministic;
6. LCIA output keeps its non-certification boundary;
7. hazardous-route physical execution remains unauthorized.
