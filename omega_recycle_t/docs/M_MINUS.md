# M⁻ — Ω-RECYCLE-T∞ R0.4

Negative memory is part of the model, not cleanup.

| ID | Failure / limitation | R0.4 state | Required next repair |
|---|---|---|---|
| M-001 | Coupled route optimization can explode combinatorially | Partially repaired: exhaustive oracle + branch-and-bound | Add performance curves and larger empirical instances |
| M-002 | Synthetic decision economics | Open | Add source-specific empirical price/cost adapters |
| M-003 | Mixture entropy is only a descriptor | Open | Add process/exergy models before thermodynamic claims |
| M-004 | Functional probability was uncalibrated | Partially repaired: Beta posterior + calibration metrics | Calibrate on inspection/history datasets with temporal splits |
| M-005 | Preservation hierarchy can bias route choice | Partially repaired: explicit baselines | Run empirical ablations and retain failures |
| M-006 | No certified lifecycle assessment | Partially repaired: LCI + external LCIA adapter | Add recognized factor-set adapters, system boundaries and method/version governance |
| M-007 | Hazardous routes require professional handling | Intentionally open | Preserve simulation-only/certified-process gate |
| M-008 | Finite B&B budget can stop before optimum | Explicitly represented | Track incumbent/bound gap over larger instances |
| M-009 | Monte Carlo posterior summaries depend on draws/seed | Explicitly represented | Add convergence diagnostics and analytic thresholds |
| M-010 | Domain UrbanMine adapters are schemas, not measurements | Open | Connect empirical electronics/battery/building stocks |
| M-011 | Greedy industrial symbiosis can be suboptimal | Repaired diagnostically: exact court + permanent counterexample | Benchmark regret distributions on real networks |
| M-012 | R0.4 transport graph is bipartite/single-stage | Open | Add multi-hop, multi-commodity, storage and time-expanded formulations |
| M-013 | Public catalog metadata can become stale | Explicitly represented | Automate source-version checks without silently mutating snapshots |
| M-014 | Snapshot hash proves identity, not semantic correctness | Explicitly represented | Add schema/unit/flag validation per source |
| M-015 | External LCIA factors may be incomplete or incompatible | Explicit unmatched-flow report | Add unit ontology and method-specific validation |

## Permanent counterexample

The two-offer/two-need symbiosis case in `test_r04_evidence.py` demonstrates that the historical greedy matcher can recover 1 unit where the exact matcher recovers 2. This counterexample must not be removed merely to make the baseline look stronger.

## Anti-overclaim rule

A higher route score, an optimization certificate, a calibration metric, a dataset hash or an LCIA characterization result each proves only its declared local contract. None independently proves sustainability, profitability, safety, regulatory compliance, causality or real-world superiority.
