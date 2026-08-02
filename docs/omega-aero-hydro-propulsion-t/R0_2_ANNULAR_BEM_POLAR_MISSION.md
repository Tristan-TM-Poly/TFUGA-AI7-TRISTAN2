# Ω-AERO-HYDRO-PROPULSION-T∞ — R0.2

## AnnularBEM-T + PolarRegistry-T + MissionGenome-T

**Status OAK:** `IMPLEMENTED + TESTED + CERTIFIED_COMPUTATIONAL_MULTIPOINT_R0_2`

**Physical status:** `NOT_FLIGHT_CERTIFIED + NOT_MARINE_CERTIFIED + NOT_EXPERIMENTALLY_VALIDATED`

R0.2 promotes the R0.1 rotor screening kernel from one uniform induced velocity and one operating point toward three coupled research objects:

1. annular axial and tangential induction;
2. provenance-aware tabulated airfoil or hydrofoil polars;
3. multipoint mission energy and constraint accounting.

Passing R0.2 tests proves reproducible software behavior under the encoded assumptions. It does not prove real rotor performance.

## 1. Annular discretization

For each interval between two blade stations, the solver constructs one annular element with midpoint radius, mean chord and mean twist. The local relative velocity is

\[
W = \sqrt{(V_\infty+v_i)^2 + [\Omega r(1-a')]^2},
\]

where:

- \(v_i\) is the local axial induced velocity;
- \(a'\) is a local tangential induction factor;
- \(\Omega\) is shaft angular velocity;
- \(r\) is the annular midpoint radius.

The inflow angle is

\[
\phi = \operatorname{atan2}(V_\infty+v_i,\Omega r(1-a')).
\]

The local angle of attack is

\[
\alpha = \beta + \beta_c - \phi,
\]

with geometric twist \(\beta\) and collective increment \(\beta_c\).

## 2. Sectional loads

For local coefficients \(C_L\) and \(C_D\), the force components use

\[
C_n = C_L\cos\phi-C_D\sin\phi,
\]

\[
C_t = C_L\sin\phi+C_D\cos\phi.
\]

The annular blade-element estimates are

\[
dT = \frac12\rho W^2 BcF C_n\,dr,
\]

\[
dQ = \frac12\rho W^2 BcF C_t r\,dr.
\]

Here \(F\) is a bounded combined tip/hub loss factor. This implementation is a research approximation, not a universal correction.

## 3. Momentum iteration

The local axial target is obtained from an annular propeller momentum balance of the form

\[
dT = 4\pi\rho rFv_i(V_\infty+v_i)\,dr.
\]

Tangential induction is updated from a local angular-momentum relation. Both quantities use bounded under-relaxation and explicit residual tracking.

Each section records:

- iterations;
- convergence status;
- final residual;
- induced velocities;
- loss factor;
- Reynolds and Mach numbers;
- polar source model;
- extrapolation status;
- thrust and torque contribution.

The model does not yet include validated high-thrust corrections, dynamic inflow, yaw, azimuthal asymmetry, free wake, blade flexibility or unsteady stall.

## 4. PolarRegistry-T

A `PolarTable` stores samples indexed by:

- angle of attack;
- Reynolds number;
- Mach number;
- lift, drag and moment coefficients;
- optional uncertainty estimates;
- source type;
- provenance.

Within a Reynolds/Mach state, coefficients are interpolated linearly in angle of attack. Nearby operating states are blended by deterministic inverse-distance weighting in \(\log_{10}(Re)\)-Mach space.

Every evaluation reports whether it extrapolated:

- outside the sampled angle range;
- outside the sampled Reynolds/Mach envelope.

Supported evidence classes include experiment, CFD, panel method, analytic model and synthetic regression fixture. The evidence class is metadata, not a guarantee of quality.

## 5. MissionGenome-T

A mission is an ordered set of phases. Each phase contains:

- duration;
- freestream velocity;
- shaft speed;
- collective pitch;
- minimum thrust;
- maximum shaft power;
- maximum tip Mach;
- importance weight.

For phase \(k\), shaft energy is

\[
E_{s,k}=P_{s,k}\Delta t_k,
\]

and useful propulsive energy is

\[
E_{u,k}=\max(0,T_kV_k)\Delta t_k.
\]

Mission efficiency is reported as

\[
\eta_m = \frac{\sum_k E_{u,k}}{\sum_k E_{s,k}},
\]

when total shaft energy is positive.

The demonstration mission contains takeoff, climb and cruise phases. It is a deterministic fixture, not an aircraft requirement set.

## 6. OAK R0.2 gates

The automated gates verify:

- exact-state polar interpolation;
- retained polar provenance;
- annular convergence;
- positive propulsive load;
- dispatch to tabulated polars;
- completion of all mission phases;
- exact mission energy aggregation;
- bounded reported mission efficiency;
- explicit refusal of physics certification.

The successful status is

```text
CERTIFIED_COMPUTATIONAL_MULTIPOINT_R0_2
```

This status applies only to the tested software claims.

## 7. Commands

```bash
omega-propulsion-r02 benchmark
omega-propulsion-r02 polar-demo
omega-propulsion-r02 annular-demo
omega-propulsion-r02 annular-demo --tabulated-polar
omega-propulsion-r02 mission-demo
```

Equivalent module execution:

```bash
python -m omega_aero_hydro_propulsion_t.r02_cli benchmark
```

## 8. Machine-readable contracts

- `schemas/propulsion_polar_table.schema.json`
- `schemas/propulsion_mission_genome.schema.json`

## 9. Remaining fidelity debt

Before engineering claims, the branch still requires:

- reference rotor comparison against traceable measurements;
- validated measured or CFD polar datasets;
- high-thrust and static-thrust treatment;
- azimuthal and unsteady wake models;
- rotor–stator and rotor–vehicle interactions;
- resolved cavitation pressure fields;
- acoustic prediction;
- structural, centrifugal, modal, fatigue and flutter analysis;
- thermal and electrical-chain coupling;
- uncertainty propagation;
- wind-tunnel, water-tunnel or bench measurements;
- qualified engineering review and applicable certification.

## 10. Next implementation frontier

R0.3 should add:

1. polar file ingestion and evidence manifests;
2. mission and rotor JSON loaders;
3. reference-case benchmark registry;
4. high-thrust correction alternatives with explicit model selection;
5. multipoint design optimization using mission energy, constraint margins and uncertainty;
6. preliminary blade structural beam model;
7. free-wake adapter boundary.
