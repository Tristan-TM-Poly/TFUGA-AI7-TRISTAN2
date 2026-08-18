# Ω-PHASE-EVOLUTION-T∞ — R0.7

## Self-Renormalizing Verified Capability Field

**Status:** executable OAK-safe prototype.

The purpose of R0.7 is to replace calendar-driven architecture roadmaps with state-driven transition decisions.

The central doctrine is:

> Do not predict the future architecture. Detect when the current representation has become the wrong regime, then propose a reversible, evidence-carrying transition.

This extends Ω-SANS-PLAFOND-T∞ R0.6 rather than creating a separate autonomy stack.

## 1. State, not calendar time

The architecture is modeled as a function of system state:

```text
Architecture = A(Xi)
```

where `Xi` includes comparable verified-work capacities plus normalized pressure, capability, regeneration, independence, observability and human-dependency signals.

The current prototype intentionally contains **no date or year field**. Identical states produce identical phase decisions regardless of calendar time.

## 2. Verified absorption bottleneck

R0.7 requires the capacity channels to be expressed in the same work-per-time unit:

```text
C = {compute, agents, humans, proof, memory, governance}
V_absorb <= min(C)
```

The minimum channel is reported as the active bottleneck. This prevents a GPU or agent-count increase from being interpreted as an ecosystem-wide capacity increase when proof, governance, memory or human collaboration remains limiting.

## 3. Transition pressure

The transition-pressure proxy is a weighted normalized aggregate:

```text
Pi = weighted_mean(
    residual_pressure,
    debt_pressure,
    latency_pressure,
    compute_cost_pressure,
    human_friction,
)
```

A regime becomes transition-critical when:

```text
Pi >= Pi_critical
```

This is an architectural heuristic, not a physical phase-transition theorem.

## 4. Criticality control

Generation is compared with verified absorption:

```text
kappa = GenerationRate / VerifiedAbsorptionRate
```

The policy distinguishes:

```text
kappa < target          -> normal regime
kappa near target       -> COMPRESS_AND_VERIFY
kappa >= overload       -> THROTTLE_GENERATION
```

R0.7 therefore encodes the stability law:

```text
GenerationRate <= VerifiedAbsorptionRate
```

as an executable control gate rather than a slogan.

## 5. Mutation gate

A high transition pressure does not automatically justify architectural mutation.

The prototype computes:

```text
MutationScore = ExpectedResidualReduction / (MigrationCost + MigrationRisk + InducedDebt)
```

The decision matrix is:

```text
pressure low, kappa low              -> STAY
pressure low, kappa near capacity    -> COMPRESS_AND_VERIFY
pressure high, mutation weak         -> COMPRESS_AND_OBSERVE
pressure high, mutation strong       -> MUTATE
kappa beyond overload                -> THROTTLE_GENERATION
```

No branch performs a deployment or remote mutation.

## 6. Order parameter

R0.7 introduces a bounded architecture-order proxy:

```text
Psi =
  VerifiedCapability
  * Regeneration
  * Independence
  * Observability
  / (1 + Debt + HumanFriction + HumanDependency)
```

It maps a state into heuristic labels:

```text
HUMAN_CENTRIC
TOOL_AUGMENTED
AGENTIC
DISTRIBUTED
SELF_RENORMALIZING
REGENERATIVE
```

These labels describe the modeled operating regime only. They are not claims of consciousness, agency, scientific superiority or real-world organizational independence.

## 7. Reversibility-first

Evidence temperature is represented by uncertainty in `[0,1]`:

```text
uncertainty up -> reversibility requirement up
```

Every proposed architectural mutation and every overload response is marked as requiring a reversible path. The engine always emits:

```text
automatic_execution = false
```

## 8. Apoptosis becomes conservation-audited distillation

R0.7 rejects the rule "delete whatever lacks immediate value".

Before compression, migration or deletion, it evaluates:

```text
eta_C = VerifiedCapability_after / VerifiedCapability_before
eta_R = Regeneration_after / Regeneration_before
rho_K = PersistentComplexity_after / PersistentComplexity_before
```

A transformation is rejected when capability or regeneration falls below configured conservation floors.

The preferred transformation is:

```text
DeleteStructure + PreserveCapability + PreserveRegeneration
```

This formalizes OAK-safe apoptosis/autophagy without converting present-value judgments into irreversible destruction.

## 9. Mutation portfolio

`MutationCandidate` ranks finite candidate transitions using residual reduction, verified capability gain, reversibility, migration cost, risk and induced debt.

This is deliberately a **ranking heuristic**, not a final authority. A candidate must still pass independent tests, canary evidence, policy/permission checks and human review for irreversible changes.

## 10. Relation to R0.6

R0.6 already provides:

- adversarial OAKBench;
- Pareto selection;
- canary promotion;
- rollback plans;
- content-addressed proof bundles;
- M+/M- evidence;
- explicit non-automatic authority.

R0.7 adds the missing upstream question:

> Should the current regime stay, compress, be throttled, or become a mutation candidate at all?

The intended future composition is:

```text
PhaseEvolutionEngine
-> candidate architecture
-> AdversarialOAKBench
-> Pareto front
-> canary
-> proof bundle
-> explicit authority gate
-> reversible migration
-> regeneration audit
```

## 11. Executable surface

Run the deterministic proposal-only demo:

```bash
python -m omega_unbounded_t.phase_evolution
```

Run the focused tests:

```bash
python -m pytest tests/test_omega_unbounded_recursive_evolution.py -q
```

The new R0.7 assertions are integrated into the existing Ω-SANS-PLAFOND recursive-evolution test target so the existing dedicated CI workflow executes them.

## 12. OAK boundaries

R0.7 does **not** prove:

- that software ecosystems obey thermodynamic phase-transition laws;
- that `Psi` is a universal order parameter;
- that the selected pressure weights are empirically calibrated;
- that a mutation candidate will improve a real production system;
- that autonomy or founder-independence has been achieved;
- that compute, agents, humans, proof, memory and governance can be compared without a declared common unit;
- that the ranking heuristic should replace Pareto analysis, domain experts or governance.

Before stronger promotion, R0.7 requires real telemetry, sensitivity analysis, counterfactual baselines, calibration against actual bottlenecks, independent reproduction and integration with the existing R0.6 proof-carrying canary path.

## 13. Next falsifiable increments

1. Calibrate pressure weights from repository/CI telemetry rather than fixed defaults.
2. Add hysteresis so phase labels do not chatter around thresholds.
3. Add multi-window trend derivatives and early-warning signals.
4. Couple mutation candidates to R0.6 adversarial scenarios and proof bundles.
5. Add a schema-backed phase-decision evidence artifact.
6. Compare scalar mutation ranking against Pareto and ablation baselines.
7. Test whether regeneration audits preserve externally measured capability after real code distillation.
8. Add founder-independence dimensions only when operational, governance, security, capital and succession evidence exist.

The R0.7 scientific claim is intentionally narrow:

> A finite, deterministic and reversible decision kernel can make architecture-phase proposals from explicit bottleneck, pressure, criticality, mutation-evidence and regeneration-conservation signals without using calendar time as the trigger.
