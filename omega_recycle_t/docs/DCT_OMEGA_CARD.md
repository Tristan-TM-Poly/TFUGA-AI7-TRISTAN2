# DCT-Ω Card — Ω-RECYCLE-T∞ R0.2

```yaml
id: OMEGA-RECYCLE-T-INF-R0.2
name: Structure-Preserving Recycling and Regeneration
repo_path: omega_recycle_t/
status: D
definition: >
  A decision-support framework that models end-of-life objects as resource
  hypergraphs and selects recovery routes that trade recovered value against
  cost, energy, risk, externalities, quality and destruction of useful structure.
hypotheses:
  - useful structure can be assigned an explicit preservation prior
  - route quality and future-cycle value should influence recovery decisions
  - material mixture entropy is a useful descriptor, not a complete recycling cost model
  - coupled budgets can change the optimum relative to independent component choices
equation_or_model: J = V - C - lambda_E E - lambda_R R - X + lambda_P P + lambda_F F
code_or_calculation: omega_recycle_t/omega_recycle/
test_path: omega_recycle_t/tests/
proof_path: null
risk_boundary:
  - no hazardous physical-processing instructions
  - no claim of physical law
  - no lifecycle-assessment certification
  - no industrial performance claim without baselines and data
m_minus:
  - exact coupled optimizer is exponential and limited to small benchmarks
  - synthetic prices are illustrative
  - mixture entropy is not thermodynamic entropy of the complete process
  - greedy symbiosis matching is not globally optimal
next_experiment: >
  add scalable constrained optimization and Bayesian uncertainty, then benchmark
  on an open provenance-tracked dataset against mass-only and value-only baselines
promotion_decision: prototype
```

## Claim discipline

The executable result demonstrates that the formal decision rules run deterministically and obey encoded safety constraints. It does not demonstrate that the rules are optimal for a real recycling plant.

## Falsification targets

1. Find cases where the structure-preservation prior causes a worse economic/environmental route.
2. Sweep uncertain functional probability and measure route-switch thresholds.
3. Compare local decisions with the exact coupled oracle.
4. Compare against mass-recovery-only and value-only baselines.
5. Measure greedy symbiosis regret against an exact matcher on small cases.
6. Record counterexamples in M⁻ rather than tuning them away.
