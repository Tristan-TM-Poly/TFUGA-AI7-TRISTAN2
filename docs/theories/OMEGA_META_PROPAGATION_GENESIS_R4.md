# Ω-META-PROPAGATION-GENESIS-T∞Ω — R4 executable crystallization

Status: **candidate / toy computational theory**.  
Scope: propagation, reachability and possibility engineering as a cross-domain software calculus.  
OAK rule: no cross-domain analogy is a physical law unless domain-specific derivation and evidence exist.

## Mother definition

A propagation is represented operationally as a distributed transformation that changes the reachable state set:

\[
P: (S,\mathcal R,C,A,E) \rightarrow (S',\mathcal R')
\]

where `C` are constraints, `A` authority/permissions and `E` evidence.

The central engineering objective is not maximum spread. It is a minimum-sufficient transformation that maximizes verified useful state change while bounding dangerous reachability, epistemic inflation, cost, risk and irreversibility.

## Hierarchy

```text
Flow
  ⊂ Propagation
  ⊂ DistributedTransformation
  ⊂ ReachabilityTransformation
  ⊂ PossibilityEngineering
```

This is a modeling hierarchy, not an assertion that every physical/social/software process shares the same governing equations.

## Canonical objects

### PropagationGenome
Carries payload type, source, targets, topology, constraints, permissions, evidence, stop rules and rollback.

### PropagationPassport
Carries origin, transformation lineage, evidence, integrity metadata, validity domain, expiry and revocation rules.

### TransformationGenome
Carries before/after state, intent, claims, evidence, risk, authority, rollback and observed reality gap.

### ReachabilityGenome
Carries current reachable states, desired/forbidden states, actions, constraints and future-option deltas.

### CompilerGenome / PolicyGenome
Carries the logic that generates and selects propagation programs. Generator and judge remain separated.

## Executable R4 kernel

The prototype in `prototypes/omega_propagation_t` currently implements:

1. route selection over explicit latency/fidelity/risk weights;
2. delivered quantity under abstract gain/fidelity/capacity parameters;
3. exact small-graph minimum edge cut;
4. a toy propagation-number diagnostic;
5. epistemic-inflation detection;
6. a fail-closed stop rule;
7. a meta-depth gate requiring net measured gain;
8. benchmark receipts that explicitly distinguish test PASS from proof.

## Meta-automation loop

```text
OBSERVE
→ REPRESENT
→ RESIDUALIZE
→ GENERATE
→ COUNTERFACTUALIZE
→ ATTACK
→ VERIFY
→ SELECT
→ AUTHORIZE
→ PROPAGATE
→ MONITOR
→ REALITY-GAP
→ LEARN
→ DISTILL
→ PRUNE
→ REGENERATE
```

### Meta-generation stop rule

Create meta-level `n+1` only if:

\[
\Delta VC + \Delta RG + \Delta TR + \Delta FO
>
\Delta CX + \Delta RK + \Delta DB + \Delta CP
\]

where the terms denote verified capability, regenerability, transfer, future options, complexity, risk, debt and compute.

If the inequality is not satisfied, choose `STOP`, `MERGE`, `COMPRESS` or `PRUNE`.

## Meta-constitution

Hard conceptual invariants:

- `Generated != Verified`
- `Generator != Judge`
- `Capability != Authority`
- `Simulation != Reality`
- `Reach != Impact`
- `Replication != Validation`
- `LocalPASS != GlobalPASS`
- `ClaimScope <= EvidenceScope`
- `SelfModification != SelfApproval`
- `MetaDepth => MeasuredGain`

Any future automation that weakens verification independence or increases irreversibility must face a higher evidence threshold.

## Propagation Diff

Any transformation should be decomposable as:

```text
ContentDiff
SemanticDiff
CapabilityDiff
EvidenceDiff
AuthorityDiff
RiskDiff
TopologyDiff
```

A negligible text diff can still imply a large authority or capability diff.

## Dynamic resolution

Resolution should increase where causal sensitivity, uncertainty, risk or evidence need are high:

\[
Resolution(x,t) \propto Sensitivity \times Uncertainty \times Risk \times EvidenceNeed.
\]

This is an allocation heuristic. It is not quantum mechanics unless a separate, explicit quantum-information model satisfies the relevant physical/mathematical axioms.

## Research program

### R4 — current
Toy graph kernel + OAK tests + benchmark.

### R5
Hyperedges, typed payload transformations, provenance receipts, counterfactual route ensembles.

### R6
Residual field, adaptive resolution, phase/regime detection on synthetic graphs, ablations against ordinary shortest-path and min-cut baselines.

### R7
Domain adapters:
- software/dependency propagation;
- evidence/claim propagation;
- energy-flow toy adapter using real conservation constraints;
- environmental-impact toy adapter.

No adapter inherits validity from another domain merely because the topology looks similar.

### R8
Compiler tournament: multiple routing/model/policy generators evaluated by frozen benchmarks with independent judge logic.

## Falsification targets

The program should be rejected or reduced if:

1. the generalized calculus adds no measurable capability beyond standard graph/network methods;
2. meta-levels fail the net-gain gate;
3. cross-domain transfer does not outperform domain-specific baselines;
4. provenance overhead dominates utility;
5. adaptive resolution does not reduce compute at matched accuracy;
6. proposed curvature/phase metrics fail to predict useful interventions;
7. simpler existing algorithms dominate the implementation.

## Minimal sufficient architecture

The current candidate kernel is intentionally small:

```text
Graph
+ Route objective
+ Containment cut
+ Stop rule
+ Evidence guard
+ Meta-depth gate
+ Benchmark
```

Everything else is a candidate extension and must earn persistence through benchmarked gain.

## Doctrine

> Do not maximize propagation. Maximize verified useful changes in reachable states using the minimum sufficient propagation, while preserving evidence, authority boundaries, reversibility and future options.
