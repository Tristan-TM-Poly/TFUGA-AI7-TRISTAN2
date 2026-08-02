# Ω-PROPULSION R0.3 Max — Unbounded System Search

**OAK status target:** `CERTIFIED_COMPUTATIONAL_SYSTEM_SEARCH_R0_3_MAX`

R0.3 Max turns the four R0.3 screening kernels into one resumable system-design search:

- `StructuralBlade-T`;
- `RobustMission-T`;
- `AcousticScreen-T`;
- `FaultEnvelope-T`.

It remains a low-order research system. It does not certify an aircraft, marine vehicle, rotor, material, fault response or acoustic performance.

## No permanent total cap

The frontier is an indexable deterministic stream rather than a pre-materialized Cartesian grid. For any non-negative integer `i`, radical-inverse coordinates generate:

- diameter scale;
- chord scale;
- pitch delta;
- RPM scale;
- a material-atlas selection.

There is no encoded final frontier cardinality. This does **not** mean infinite physical computation. Every invocation declares a finite `count`, checkpoint interval and prior chain digest. Larger campaigns continue from `next_index`.

```text
index 0 ... count-1
→ evaluate finite run
→ checkpoint next_index + SHA-256 chain
→ resume later
```

## Candidate evidence

Every candidate is evaluated against:

1. nominal annular BEM at every mission phase;
2. critical structural phase;
3. critical acoustic phase;
4. weighted robust mission cases;
5. deterministic fault scenarios.

The evidence hash covers the design vector, critical phases, objective tensor, violations and model identifiers.

## Seven-objective Pareto search

The search minimizes:

- expected shaft energy;
- rotor mass;
- acoustic screening level.

It maximizes:

- worst mission efficiency;
- minimum structural safety factor;
- robust feasible probability over declared cases;
- safe-continuation fraction over declared fault cases.

The scalar ranking is only a navigation heuristic. The non-dominated Pareto set remains the primary output.

## Material atlas boundary

The default atlas contains generic deterministic fixtures for carbon/epoxy, glass/epoxy, aluminum, titanium and laminated wood. Every entry explicitly declares `engineering_allowables: false`.

These values are not approved design allowables. Real use requires traceable material standards, coupon tests, laminate schedules, defects, joints, environment, fatigue and manufacturing evidence.

## Checkpoints and chain continuity

For candidate evidence hash `h_i` and prior chain digest `c_i`:

```text
c_(i+1) = SHA256(c_i + ":" + h_i)
```

A resumed campaign must produce the same final digest as a single uninterrupted campaign over the same ordered indices and inputs.

## CLI

```bash
omega-propulsion-r03-max benchmark
omega-propulsion-r03-max candidate --index 1000000
omega-propulsion-r03-max campaign --start-index 0 --count 32 --checkpoint-interval 8 --summary-only --relaxed
omega-propulsion-r03-max campaign --start-index 32 --count 32 --previous-digest <digest> --summary-only --relaxed
```

`--relaxed` exists for deterministic OAK search tests. It does not make a candidate safe or certified.

## Promotion path

```text
R0.3 Max system screening
→ traceable material and polar evidence
→ validated structural and acoustic models
→ free-wake / CFD / FSI
→ robust probabilistic analysis
→ bench, wind-tunnel or water-tunnel tests
→ independent engineering review
→ applicable certification
```
