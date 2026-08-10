# DCT-Ω Card — Ω-RECYCLE-T∞ R0.3

```yaml
id: OMEGA-RECYCLE-T-INF-R0.3
name: Structure-Preserving Recycling and Regeneration
repo_path: omega_recycle_t/
status: D
definition: >
  OAK-safe decision-support research kernel that represents end-of-life objects
  as resource hypergraphs, evaluates recovery trajectories, cross-checks a
  pruned solver against an exhaustive oracle, propagates functional-state
  uncertainty and exposes explicit baselines and inventory/provenance layers.
hypotheses:
  - useful structure can be represented as an explicit, ablatable preservation prior
  - route quality and future-cycle value can improve decisions on some datasets
  - constrained search can be pruned without changing the optimum when the upper bound is admissible
  - functional-state uncertainty can materially change route preference
equation_or_model: J = V - C - lambda_E E - lambda_R R - X + lambda_P P + lambda_F F
code_or_calculation: omega_recycle_t/omega_recycle/
test_path: omega_recycle_t/tests/
proof_path: omega_recycle_t/docs/R03_EVIDENCE.md
risk_boundary:
  - no hazardous physical-processing instructions
  - no claim of physical law
  - LCA inventory interface is not lifecycle impact assessment
  - Bayesian posterior is not calibrated evidence by itself
  - branch-and-bound remains exponential in the worst case
m_minus:
  - current economics and OAKBench inputs are synthetic
  - preservation prior can be harmful and must be benchmarked
  - finite search budgets can lose optimality certification
  - UrbanMine domain adapters are structural, not empirically calibrated
next_experiment: >
  ingest a provenance-tracked public dataset, measure baseline regret, calibrate
  uncertainty, and add network capacity/transport constraints
promotion_decision: prototype
```

## Falsification targets

1. Find a small problem where branch-and-bound disagrees with the exhaustive oracle.
2. Find datasets where no-preservation, mass-only or value-only beats the canonical policy.
3. Quantify route switches under posterior uncertainty.
4. Measure empirical calibration error for functional-state probabilities.
5. Compare UrbanMine estimates with observed recovered quantities.
6. Keep any counterexample in M⁻ instead of tuning it away.
