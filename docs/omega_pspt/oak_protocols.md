# OAK Protocols for Omega-PSPT++

OAK is the claim-control layer for Tristan solid-state physics. It prevents strong names from outrunning evidence.

---

## Universal OAK ladder

```text
OAK-0 intuition/name
OAK-1 formal definition
OAK-2 simulation
OAK-3 falsifiable prediction
OAK-4 internal measurement
OAK-5 artifact-controlled measurement
OAK-6 independent replication
OAK-7 canonized robust phase
```

Every Omega-PSPT claim must store:

```text
claim: what is asserted
status: current OAK level
evidence: why the level is justified
falsifiers: what would disprove or demote it
next_test: the next highest-information experiment or simulation
negative_memory_links: similar past false positives
```

---

## Protocol H1 — Fractal geometry improves conductivity

Claim form:

```text
At equal material, mass, volume, contact geometry, and environment, a fractal/hyperloop geometry changes effective conductivity beyond ordinary porosity/percolation controls.
```

Required controls:

- same material;
- same mass or normalized mass;
- same macroscopic dimensions;
- same contact geometry;
- same fabrication route;
- same temperature and humidity;
- random porous control with matched porosity;
- non-fractal control with matched surface area;
- 2-probe and 4-probe comparison.

Measurements:

```text
R_2probe, R_4probe, I(V), sigma_eff, Z(omega), thermal drift
```

Promotion:

- OAK-1: graph/geometric model defined.
- OAK-2: resistor network simulation shows effect.
- OAK-3: quantitative prediction for control-vs-fractal sample.
- OAK-4: one internal measurement consistent with prediction.
- OAK-5: controls reject contact/surface/porosity artifacts.
- OAK-6: independent replication.

Falsifiers:

- effect disappears in 4-probe geometry;
- matched random porous control performs equally;
- signal explained by contact area;
- effect not reproducible across samples.

---

## Protocol H2 — Hyperloops create measurable magnetic/RF response

Claim form:

```text
The cycle hierarchy Gamma_n creates measurable RF/magnetic resonances not predicted by porosity alone.
```

Core invariants:

```text
beta_1 = |E| - |V| + c
L_T(n) = sum_k w_k log(1 + |Gamma_k|)
Z_T(omega) = network impedance over R, L, C, and mutual couplings
```

Measurements:

```text
S11(omega), S21(omega), Z(omega), mu_eff(omega), M(B), chi(T)
```

Promotion requires:

- loop-count model;
- RF/impedance simulation;
- predicted resonance tree;
- measured resonances;
- matched non-fractal loop controls;
- loss/Q-factor analysis.

Falsifiers:

- resonances match only sample size, not loop hierarchy;
- resonances vanish with proper calibration;
- response explained by ordinary parasitic capacitance/inductance;
- no scaling with iteration depth.

---

## Protocol H3 — Fractal topological phase candidate

Claim form:

```text
A non-periodic/fractal support carries robust topological boundary, corner, or defect modes with a non-trivial marker.
```

Minimum simulation evidence:

```text
spectral gap + localized boundary/corner states + disorder robustness + real-space topological marker
```

Tests:

- finite-size scaling;
- boundary condition comparison;
- disorder sweep;
- trivial control Hamiltonian;
- real-space marker stability;
- mode localization maps.

Falsifiers:

- states are ordinary dangling-bond modes;
- gap closes under small perturbations;
- no marker distinguishes trivial control;
- finite-size artifact only.

---

## Protocol H4 — Omega-TFTS superconducting topological fractal candidate

Claim form:

```text
A fractal/hyperloop solid or network supports superconducting and topological signatures simultaneously.
```

Simulation requirements:

```text
BdG gap candidate
edge/corner/defect modes
topological marker
phase stiffness or Josephson network coherence
robustness to controlled disorder
```

Experimental requirements before strong claim:

```text
zero resistance or strong transport evidence
Meissner/magnetic screening
spectroscopic gap
critical current I_c
critical field B_c
thermodynamic anomaly when feasible
replication across samples
artifact rejection
```

Forbidden shortcut:

```text
R -> 0 alone is not enough.
```

Falsifiers:

- contact short;
- filamentary superconductivity from impurity;
- no Meissner signal;
- no gap;
- no critical current;
- non-reproducible sample;
- topological marker trivial;
- edge/corner states are geometric dangling modes only.

---

## Protocol H5 — CVCD detects phase transitions

Claim form:

```text
FFWT-HAC-CVCD detects phase transitions or material classes with fewer features and better robustness than baseline descriptors.
```

Datasets:

```text
Raman, XRD, IR, impedance, transport, susceptibility, synthetic simulations
```

Baselines:

- raw peak features;
- PCA/UMAP features;
- Fourier/wavelet features;
- classical statistics;
- supervised ML baseline.

Metrics:

```text
accuracy, F1, calibration, robustness-to-noise, cross-sample generalization, feature count, interpretability
```

Falsifiers:

- CVCD performs no better than simpler descriptors;
- CVCD unstable under small noise;
- extracted invariants are not interpretable;
- performance leaks from data preprocessing or labels.

---

## OAK decision rule

Promotion requires both positive evidence and negative-memory clearance:

```text
Promote(Phi) iff EvidenceScore(Phi) >= threshold(level) and ArtifactScore(Phi, M_minus) <= tolerance
```

Demotion is automatic when a stronger falsifier appears.
