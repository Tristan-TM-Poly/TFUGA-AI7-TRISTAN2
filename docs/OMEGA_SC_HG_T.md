# Ω-SC-HG-T∞ — Bond–Orbital–Phonon Superconductivity Hypergraph

## Status

**Research software / theory scaffold.** This module does not claim a new superconductor, does not replace DFT/DFPT or Eliashberg calculations, and never upgrades a theoretical prediction into experimental evidence.

## Motivation

The August 2026 PRL report on AA-stacked bilayer borophene predicts an elemental-superconductor transition temperature of **68 K at ambient pressure** after screening more than 9,000 stacking arrangements. The public report attributes the improvement to direct covalent B–B interlayer bonds and explicitly states that experimental validation remains necessary.

Primary source: Meng-hui Wang et al., *Bilayer Borophenes Establish a New Upper Limit for Elemental Superconducting Transition Temperatures*, Physical Review Letters (2026), DOI `10.1103/8l19-rdn2`.

Public summary: https://phys.org/news/2026-08-boron-layers-superconductivity-theoretical.html

## Core hypothesis to test

The transferable design object is not merely composition or stacking. It is the coupled motif

`bond topology -> orbital topology -> Fermi topology -> phonon topology -> EPC -> pairing -> phase ordering`.

This is a **research hypothesis**, not an established universal law.

## Executable object

`SuperconductingCandidate` separates:

- inter/intralayer bond channels;
- orbital weights near the Fermi level;
- phonon channels with `lambda_ep`, `omega_log_k`, and an explicit stability margin;
- an externally supplied phase-ordering ceiling;
- synthesis, defect, and substrate robustness descriptors.

The cheap `pairing_tc_k()` function is a McMillan/Allen-Dynes-style **screening proxy only**. High-value candidates must be re-evaluated with converged first-principles and, where appropriate, anisotropic Eliashberg calculations.

## OAK gates

1. **Evidence gate** — theoretical, simulated, experimental and inferred claims remain distinct.
2. **Dynamic-stability gate** — negative stability margins reject a candidate from promotion.
3. **Pairing/phase gate** — `usable_tc = min(pairing estimate, externally supplied phase-ordering ceiling)`; the package does not infer BKT from pairing data.
4. **Uncertainty gate** — report a Tc envelope over `mu*`, EPC and phonon-frequency perturbations, rather than a single brittle number.
5. **Practicality gate** — synthesis/defect/substrate robustness enter ranking independently of nominal Tc.
6. **Counterfactual gate** — causal ablations require a separately computed intervention state; the code does not invent the physics of deleting a bond.

## Search architecture

`candidate generator -> chemistry/geometry gate -> stability -> EPC activity -> OAK envelope -> Pareto front -> expensive validation`

The search keeps a Pareto frontier across usable Tc, robust lower-tail Tc, synthesis, defect robustness and substrate robustness. This prevents a spectacular but fragile nominal Tc from automatically dominating a more realizable candidate.

## Borophene evidence seed

`borophene_2026_seed()` records only facts supported by the public paper metadata/report:

- predicted Tc = 68 K;
- ambient-pressure theoretical prediction;
- AA-stacked bilayer borophene;
- direct covalent B–B interlayer bonding as a proposed enhancement mechanism;
- experimental replication still required.

It intentionally does **not** fabricate `lambda`, `omega_log`, defect tolerance, BKT temperature or synthesis probability when those values have not been ingested from primary calculations.

## Next high-value extensions

- import real `alpha^2 F(omega)` data and integrate lambda/omega-log from spectra;
- anisotropic k/q-resolved EPC hyperedges;
- automated convergence ledgers for k/q meshes, pseudopotentials and `mu*`;
- phonon anharmonicity and soft-mode red-team checks;
- explicit superfluid stiffness / BKT adapters for genuinely 2D candidates;
- substrate, strain, doping and defect counterfactual campaigns;
- isotope-effect experiment planner;
- linkage to Ω-PCT∞, Ω-FCRYST-T, Ω-VTP-T and Ω-STACK-T∞.

## OAK falsifiers

Promote the design rule only if it survives families where interlayer covalent bonding is present but Tc does **not** increase, and families where high Tc emerges without that motif. Record both in M−.
