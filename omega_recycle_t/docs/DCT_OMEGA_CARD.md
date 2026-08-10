# DCT-Ω Card — Ω-RECYCLE-T∞ R0.1

```yaml
id: OMEGA-RECYCLE-T-INF-R0.1
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
  - component-wise independence omits plant and transport coupling
  - synthetic prices are illustrative
  - material entropy is not thermodynamic entropy of the complete process
next_experiment: >
  add coupled capacity and transport constraints, then benchmark on an open,
  provenance-tracked dataset against a mass-only recycling baseline
promotion_decision: prototype
```

## Claim discipline

The executable result demonstrates that the formal decision rule runs deterministically and obeys the encoded safety constraints. It does not demonstrate that the rule is optimal for a real recycling plant.

## First falsification targets

1. Find cases where the structure-preservation prior causes a worse economic/environmental route.
2. Sweep uncertain functional probability and determine route-switch thresholds.
3. Compare with a mass-recovery-only baseline.
4. Add process-specific data and measure sensitivity to energy and risk weights.
5. Record every counterexample in M⁻ rather than tuning it away.
