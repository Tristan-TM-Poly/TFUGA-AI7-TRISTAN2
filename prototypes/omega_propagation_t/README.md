# Ω-PROPAGATION-TRISTAN-T∞ — executable kernel R4

A deliberately small, falsifiable prototype for Tristan's propagation / reachability / possibility-engineering line of work.

## What this prototype claims

It provides a **toy computational kernel**, not a universal physical law. It implements:

- typed edge attributes for latency, fidelity, risk, gain and capacity;
- explicit multi-objective route selection;
- exact small-graph edge cuts for containment experiments;
- a toy branching/propagation metric;
- epistemic-inflation detection;
- a fail-closed stop rule;
- a meta-depth gate: a new meta-layer is kept only if measured benefit exceeds complexity/risk/debt/compute cost;
- benchmark receipts with an explicit OAK disclaimer.

## What it does **not** claim

- graph propagation is not automatically wave mechanics, epidemiology, social diffusion or thermodynamics;
- `gain` is an abstract toy parameter unless a domain adapter supplies conservation laws;
- passing tests is not scientific proof;
- simulated reach is not observed impact;
- capability is not authority.

## Core invariants

1. `Generated != Verified`
2. `Capability != Authority`
3. `Simulation != Reality`
4. `Reach != Impact`
5. `Replication != Validation`
6. `LocalPASS != GlobalPASS`
7. `ClaimScope <= EvidenceScope`
8. `MetaDepth => MeasuredGain`
9. `NoMeasuredGain => Compress | Merge | Prune`
10. irreversible or high-blast-radius actions require stronger verification.

## Quick run

```bash
cd prototypes/omega_propagation_t
python -m unittest discover -s tests -v
python run_benchmark.py
```

No external dependencies are required.

## R4 architecture

```text
Intent
  -> PropagationGenome
  -> Graph/Reachability representation
  -> Candidate routes / cuts
  -> Counterfactual comparison
  -> OAK checks
  -> Stop/Execute decision
  -> Receipt
  -> Residual / M+ / M-
  -> Meta-depth gate
```

The next justified extension is not "more meta" by default. It is whichever residual scores highest on verified value-of-experiment per cost/risk.
