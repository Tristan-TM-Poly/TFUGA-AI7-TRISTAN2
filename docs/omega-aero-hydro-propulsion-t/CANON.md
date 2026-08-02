# Ω-AERO-HYDRO-PROPULSION-T∞ — Canon R0.1

**Status OAK:** `FORMALIZED + IMPLEMENTED_LOW_ORDER + NOT_FLIGHT_CERTIFIED + NOT_MARINE_CERTIFIED`

This branch connects Ω-FLUID-T∞² to propellers, rotors, fans, pumps, turbines and future aero-engine components through a deliberately low-order, reproducible design kernel.

## R0.1 executable scope

- typed fluid media, blade stations, rotor geometries and operating points;
- smooth analytic airfoil polar used only as a deterministic screening surrogate;
- blade-element sectional loads;
- uniform actuator-disk induced velocity;
- Prandtl-style tip-loss screening;
- thrust, torque, power, advance ratio and nondimensional coefficients;
- tip-speed and tip-Mach gates;
- hydrodynamic cavitation-number and pressure-margin screening;
- deterministic multiobjective grid search and Pareto extraction;
- OAK benchmark, tests, schema, CLI, example and CI.

## Master coupling

\[
\Omega\text{-PROPULSION-T}
=
\Omega\text{-FLUID-T}
\otimes
\Omega\text{-THERM-T}
\otimes
\Omega\text{-SOLID-T}
\otimes
\Omega\text{-MATERIAL-T}
\otimes
\Omega\text{-CONTROL-T}.
\]

R0.1 implements only the first low-order fluid/rotor slice. Structural stress, fatigue, flutter, combustion, heat transfer, emissions, certification and manufacturing qualification remain outside its validated scope.

## Blade genome

A rotor is encoded by blade count, hub/tip radii and ordered stations

\[
\mathcal P=(B,R_h,R_t,\{r_i,c_i,\beta_i,A_i\}).
\]

The station angle is measured from the rotor plane. The local angle of attack is the geometric station angle plus collective pitch minus inflow angle.

## Low-order force model

For each annulus, the implementation evaluates relative speed, analytic lift/drag coefficients and resolves them into axial force and torque. A uniform induced velocity is updated from an actuator-disk relation. This is a screening model—not full BEM, RANS, LES, DNS, free-wake, aeroelastic or multiphase CFD.

## Optimization doctrine

The grid optimizer ranks candidates using normalized thrust, efficiency, power and a tip-Mach noise proxy. The ranking score is a navigation heuristic, not physical truth or regulatory evidence. Pareto candidates must later be checked with higher-fidelity analysis.

## Required next couplings

1. measured or XFOIL/CFD airfoil-polar ingestion with provenance;
2. annular axial/tangential induction and Glauert corrections;
3. free-wake and rotor–stator interaction;
4. compressible nozzle, inlet, compressor and turbine maps;
5. cavitating multiphase CFD;
6. FSI, modal analysis, fatigue and flutter;
7. thermal/combustion cycle analysis;
8. adjoint and robust optimization;
9. geometry export and manufacturing constraints;
10. experimental validation ledgers.
