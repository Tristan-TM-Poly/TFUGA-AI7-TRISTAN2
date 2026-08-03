# Ω-PROPULSION R0.5 Max — WakeGraph, ArchitectureCompiler and Evidence Ladder

## Status

`COMPUTATIONAL_RESEARCH_ARCHITECTURE`

R0.5 extends the merged R0.1–R0.4 stack with three executable layers:

1. `WakeGraph-T` — prescribed helical vortex filaments with a regularized finite-segment Biot–Savart kernel;
2. `ArchitectureCompiler-T` — transparent mission-to-propulsion-architecture ranking;
3. `EvidenceLadder-T` — anti-overclaim contracts separating analytic models, system screening, stress campaigns, vortex proxies, high-fidelity numerical evidence, experiments and engineering review.

R0.5 does **not** add validated CFD, a relaxed free wake, FSI, wind-tunnel or tow-tank data, certified material allowables, airworthiness, seaworthiness or regulatory approval.

## 1. WakeGraph-T

The annular BEM sections produce a low-order circulation proxy:

```text
Γ ≈ 0.5 · Cl · Vrel · chord
```

For each annulus and blade, R0.5 creates a prescribed contracting helix. Every segment stores:

- source annulus;
- blade index;
- circulation proxy;
- regularized core radius;
- start and end coordinates;
- deterministic filament and segment identifiers.

A finite straight-vortex Biot–Savart primitive estimates induced velocity at declared probes. The numerical core removes the singularity at a segment endpoint.

### Explicit limitations

- the wake geometry is prescribed rather than relaxed dynamically;
- circulation comes from low-order blade-element sections;
- the core is numerical, not a calibrated viscous diffusion law;
- turbulence, unsteady separation, blade-vortex interaction and wake instability are absent;
- no claim of CFD, free-wake validation or experimental accuracy is made.

## 2. ArchitectureCompiler-T

A `PropulsionMissionIntent` declares:

- required thrust;
- cruise velocity;
- installation area;
- efficiency, acoustic, compactness, redundancy and maintainability priorities;
- cavitation and vectoring priorities where relevant.

The compiler evaluates transparent templates for air and water, including:

- open propellers;
- ducted fans or ducted marine propellers;
- distributed electric propulsion;
- contra-rotating systems;
- boundary-layer-ingesting fans;
- waterjets;
- podded azimuth propulsors.

The score is a deterministic heuristic. It chooses which analyses deserve investment; it does not prove actual efficiency, noise, cavitation resistance, reliability or mission feasibility.

Domain mismatch, installation-area pressure, redundancy, vectoring and cavitation priorities are explicit gates. No candidate is silently forced to pass.

## 3. EvidenceLadder-T

R0.5 formalizes the following classes:

```text
F0_ANALYTIC
F1_SYSTEM
F2_STRESS
F3_VORTEX_PROXY
F4_HIGH_FIDELITY_NUMERICAL
F5_EXPERIMENT
F6_ENGINEERING_REVIEW
```

Every receipt requires:

- a unique receipt ID;
- a SHA-256 artifact digest;
- provenance;
- method;
- declared limitations;
- tier-specific metadata.

### F4 numerical gate

A claimed high-fidelity numerical receipt is blocked without:

- solver identity;
- governing equations;
- boundary conditions;
- at least three mesh levels;
- residual convergence evidence.

Even when accepted, solver verification and validation remain separate concerns.

### F5 experiment gate

An experiment receipt is blocked without:

- facility;
- instrumentation;
- calibration identifier;
- uncertainty budget;
- retained raw data.

Independent reproduction is tracked separately.

### F6 review gate

Engineering review is scope-bounded. The ledger refuses to grant airworthiness, seaworthiness or regulatory certification. A software report cannot set `certification_claim=true`.

## 4. Deterministic proof surface

R0.5 tests:

- exact filament and segment cardinality;
- deterministic wake hashes;
- finite induced velocities;
- zero-RPM empty wake;
- singularity guard at vortex endpoints;
- unique architecture templates;
- air/water domain routing;
- deterministic architecture rankings;
- legitimate all-candidates-rejected outcomes;
- contiguous F0→F3 evidence;
- missing-lower-tier detection;
- phantom CFD rejection;
- experiment-without-raw-data rejection;
- certification-claim rejection;
- duplicate receipt rejection;
- cumulative R0.1–R0.5 OAK regression.

## 5. Commands

```bash
omega-propulsion-r05 benchmark
omega-propulsion-r05 wake-demo --summary-only
omega-propulsion-r05 architecture-demo --domain air
omega-propulsion-r05 architecture-demo --domain water
omega-propulsion-r05 evidence-demo
```

Direct module equivalents:

```bash
python -m omega_aero_hydro_propulsion_t.r05_cli benchmark
python -m omega_aero_hydro_propulsion_t.r05_cli wake-demo --summary-only
```

## 6. OAK target

```text
CERTIFIED_COMPUTATIONAL_WAKE_ARCHITECTURE_EVIDENCE_R0_5
```

This status means deterministic software invariants passed. It does not certify a physical design.

## 7. Next falsifiable layers

R0.6 should add adapters and comparison harnesses rather than merely renaming the proxy as higher fidelity:

1. relaxed free-wake iteration with convergence and wake-age sensitivity;
2. rotor–rotor and rotor–vehicle interaction graph;
3. external CFD receipt importer with mesh and boundary-condition audit;
4. experimental data package and uncertainty-budget schema;
5. BEM ↔ vortex proxy ↔ CFD ↔ experiment discrepancy tensor;
6. calibrated surrogate models with out-of-distribution detection;
7. aeroelastic and acoustic evidence as separate, non-collapsed ledgers.
