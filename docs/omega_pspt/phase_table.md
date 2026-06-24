# Omega-PSPT++ Phase Table

This table keeps speculative names useful while forcing each phase to carry observables, falsifiers, and OAK status.

| ID | Phase family | Candidate name | Core idea | Primary invariants | Minimal tests | Default status |
|---|---|---|---|---|---|---|
| A1 | Structural | Crystal-CVCD | Crystals classified by compressed multiscale signatures, not only by raw peaks. | XRD-CVCD, pair correlation, symmetry residual | XRD/Raman classification vs baseline | OAK-1 |
| A2 | Structural | Quasi-HGFM | Long-range order without ordinary periodicity, represented by hypergraph invariants. | diffraction CVCD, quasiperiodic score | diffraction, structure factor | OAK-1 |
| A3 | Structural | Glass-Fractal | Disordered solids with hidden multiscale correlations. | g(r), FFWT coherence, spectral dimension | pair correlation, Raman/IR, transport | OAK-1 |
| A4 | Structural | High-Entropy-CVCD | Disorder/composition complexity becomes a search space for robust properties. | mixing entropy, disorder descriptors, response variance | composition sweep, robustness tests | OAK-1 |
| B1 | Electronic | Flat-Band Tristan | Narrow bands amplify interactions and geometry. | bandwidth W, U/W, DOS, quantum metric | tight-binding/DFT surrogate, DOS | OAK-1 |
| B2 | Electronic | Moire-Tristan | Twist/moire superlattices generate tunable phase diagrams. | twist angle, filling, bandwidth, Berry curvature | spectrum vs angle/filling | OAK-1 |
| B3 | Electronic | Hypermoire | Multiple moire scales coupled into a hierarchy. | lambda_i, lambda_ij, multiscale beat score | geometry + spectrum sweep | OAK-0/1 |
| B4 | Electronic | Percolation-Tristan | Transport emerges from fractal connectivity and bottlenecks. | p_c, cycle rank, conductance, IPR | resistor network, 4-probe controls | OAK-1 |
| C1 | Topological | Chern-Tristan | Non-zero Chern marker and robust edge response. | Chern number/marker, Berry curvature | spectral gap + edge modes | OAK-1 |
| C2 | Topological | Z2-Tristan | Time-reversal topological candidate. | Z2 marker, helical boundary signature | gap + protected states | OAK-1 |
| C3 | Topological | Fractal-Topological | Topological markers in non-periodic/fractal supports. | real-space marker, corner/edge states, D_f | finite-size scaling + disorder robustness | OAK-1 |
| C4 | Topological | Fractional-Order Topology | Boundary/corner dimensionality may be non-integer in fractal supports. | d_boundary, D_f, localization map | corner-state scaling | OAK-0/1 |
| D1 | Fractal | Cantor Conductive | Cantor-like conductor used as simple testbed. | D_f, p_c, R_eff, impedance tree | resistor/impedance simulation | OAK-1 |
| D2 | Fractal | Sierpinski Conductive | Fractal holes generate localization and multiscale modes. | D_f, spectral dimension, IPR | spectrum + impedance + transport | OAK-1 |
| D3 | Fractal | Menger Magnetic | 3D porous hyperloop structure with magnetic/RF response. | cycle rank, loop hierarchy, chi, S-parameters | RF/magnetic simulation | OAK-1 |
| D4 | Hyperloop | LC/RLC Hyperloop | Each loop acts as coupled resonator. | omega_gamma, Q_gamma, Z(omega), losses | impedance spectrum | OAK-1 |
| D5 | Hyperloop | Josephson-Fractal Candidate | If proximized/superconducting links exist, fractal Josephson networks may form. | E_J, I_c, phase stiffness, frustration | Josephson network simulation | OAK-0/1 |
| E1 | Superconducting | SC-CVCD | Known superconducting signatures detected by invariant compression. | R(T), chi(T), gap, I_c, B_c | transport + Meissner + gap | OAK-1 |
| E2 | Superconducting | Flat-Band SC | Geometry-assisted superconducting stiffness in flat bands. | D_s geom, quantum metric, gap | BdG/mean-field + stiffness | OAK-1 |
| E3 | Superconducting | High-Entropy SC | Disorder-controlled superconducting robustness. | S_mix, T_c, H_c2, J_c | composition sweep + controls | OAK-1 |
| E4 | Superconducting | Omega-TFTS | Fractal topological superconductor candidate. | Delta, topological marker, edge/corner states, Meissner | strict SC checklist | OAK-0/1 |
| F1 | Algebraic descriptor | Complex Phase | Phase/amplitude/interference descriptor. | complex coherence, impedance phase | spectral/impedance data | OAK-1 |
| F2 | Algebraic descriptor | Quaternionic SOC | Compact spin/rotation/texture representation. | quaternionic correlation | spin texture classification | OAK-1 |
| F3 | Algebraic descriptor | Octonionic Residue | Non-associative-style residue for coupled data channels. | associator norm | predictive improvement test | OAK-0/1 |
| F4 | Algebraic descriptor | Sedenion Zero-Divisor Percolation | Local activity with weak global response. | zero-response ratio, blocked percolation score | local/global response comparison | OAK-0/1 |
| G1 | Information | CVCD-Stable Phase | Same phase under probe/scale/noise changes. | invariant stability score | bootstrap + cross-probe validation | OAK-1 |
| G2 | Information | Bayes-Tristan Phase | Phase as posterior vector over truth/fertility/testability. | B_T vector | evidence update simulation | OAK-1 |
| G3 | Information | OAK-Certified Phase | Phase promoted only by evidence. | OAK level, falsifier closure | independent replication | OAK-1 |

---

## Promotion rule

A phase cannot move upward only by name density. It must satisfy:

```text
claim_level <= evidence_level
```

Recommended claim labels:

```text
vision -> candidate -> simulated_candidate -> measured_candidate -> controlled_candidate -> replicated_phase
```

---

## Negative-memory falsifier bank

Common false positives that must be checked before promotion:

- contact resistance or short circuits;
- contamination or unintended inclusions;
- finite-size artifacts;
- thermal drift;
- ordinary percolation misread as topology;
- ordinary resonance misread as quantum phase;
- noise-filter artifact misread as CVCD invariant;
- single-sample anomaly;
- geometry-driven surface-area change misread as intrinsic phase;
- uncontrolled magnetic impurities.
