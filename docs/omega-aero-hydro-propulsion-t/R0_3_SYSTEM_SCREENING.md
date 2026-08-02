# Ω-PROPULSION R0.3 — StructuralBlade + RobustMission + AcousticScreen + FaultEnvelope

**OAK status:** `IMPLEMENTED_SYSTEM_SCREENING / NOT_ENGINEERING_CERTIFIED`

R0.3 promotes Ω-AERO-HYDRO-PROPULSION-T from aerodynamic mission screening to an initial system-design gate.

## StructuralBlade-T

The blade is reduced to effective rotating-beam sections. The model estimates material volume, rotor mass, centrifugal force, flapwise bending, torsion, von Mises screening stress, strain, safety factor and a cantilever tip-deflection proxy.

It is not laminate analysis, shell/solid FEA, joint analysis, fatigue substantiation, damage tolerance, modal analysis, flutter analysis or containment proof.

## RobustMission-T

The mission is evaluated over declared weighted cases varying density, viscosity, sound speed, freestream velocity, rotor speed and collective pitch. Every case, weight, energy, efficiency, Mach and violation remains visible.

A small deterministic case set is not a complete probability distribution or safety analysis.

## AcousticScreen-T

The acoustic layer calculates rotational frequency, blade-passing frequency, harmonics, a monotonic loading/tip-Mach proxy and spherical distance attenuation. The decibel result is comparative, not measured or certified noise.

## FaultEnvelope-T

Default cases cover RPM/power derating, pitch jam, single-blade loss and motor-out. Per-phase thrust, power, tip Mach and convergence margins are recorded. Blade loss is never marked safe without a future imbalance and transient structural model.

## Promotion chain

```text
R0.1 blade element
→ R0.2 annular BEM + polars + mission
→ R0.3 structural/robust/acoustic/fault screening
→ beam/shell/modal/fatigue/flutter models
→ unsteady CFD and validated aeroacoustics
→ calibrated vehicle/fault simulation
→ bench, wind-tunnel or water-tunnel measurement
→ qualified engineering review
→ applicable certification
```

R0.3 artifacts are research candidates and screening evidence, not proof of airworthiness, seaworthiness, structural integrity, acoustic compliance, reliability or safe continued operation.

## Next layers

1. material and section-property registry;
2. spanwise beam finite elements and centrifugal stiffening;
3. modal frequencies and Campbell diagrams;
4. rainflow and Miner damage ledgers;
5. Monte Carlo and importance sampling;
6. directional acoustic observers and measured calibration;
7. multi-rotor fault allocation and vehicle moments;
8. electric powertrain and thermal derating;
9. robust multiobjective optimization;
10. experiment and certification evidence manifests.
