# Omega-PSPT++ Experiment Cards

These cards translate the theory into concrete OAK tests.

---

## Card 1 — Geometry-to-conductance test

### Claim

A fractal/hyperloop support changes effective conductance beyond ordinary porosity.

### Inputs

```text
material: fixed
mass: matched
bounding_box: matched
contact_geometry: matched
porosity: matched across fractal/random/control samples
iteration_depth: n
```

### Measurements

```text
R_2probe
R_4probe
I(V)
Z(omega)
temperature
humidity
contact pressure
```

### Controls

- dense solid control;
- random porous control;
- periodic-hole control;
- same surface-area control;
- repeated contact mounting.

### Expected OAK result

```text
Delta sigma_eff survives contact and porosity controls.
```

### Falsifiers

```text
contact_short
surface_area_only
porosity_only
non_replicated_signal
```

---

## Card 2 — Hyperloop RF resonance tree

### Claim

Cycle-rank and loop hierarchy predict resonant features in impedance or scattering.

### Inputs

```text
Lambda_n
beta_1(n)
loop_counts_by_scale
material conductivity
magnetic permeability
sample size
```

### Measurements

```text
S11(omega)
S21(omega)
Z(omega)
Q(omega)
loss_tangent
```

### Controls

- same outline without hierarchy;
- random loop control;
- periodic loop array;
- non-conductive geometry control.

### Expected OAK result

```text
resonance families scale with loop hierarchy, not only sample size.
```

---

## Card 3 — Fractal topological simulation

### Claim

A fractal support can host robust boundary/corner/defect modes in a suitable Hamiltonian.

### Simulation inputs

```text
lattice: Sierpinski/Menger/Cantor product
H_0: tight-binding or parent topological Hamiltonian
disorder_strength: sweep
boundary_condition: open/closed comparison
```

### Outputs

```text
spectrum
gap
mode localization map
IPR
real-space topological marker
finite-size trend
```

### Falsifiers

```text
no_gap
dangling_bond_only
no_marker_difference
finite_size_only
```

---

## Card 4 — Omega-TFTS candidate sequence

### Claim

A fractal/hyperloop support with pairing and spin-orbit terms can form a topological superconducting candidate.

### Simulation path

1. Generate fractal support.
2. Build nearest-neighbor hopping.
3. Add spin-orbit term.
4. Add Zeeman or magnetic texture term.
5. Add pairing term.
6. Build BdG block.
7. Compute spectrum.
8. Map edge/corner states.
9. Compute real-space marker.
10. Sweep disorder.

### Experimental path before strong claim

```text
R(T)
Meissner/screening
spectroscopic gap
I_c
B_c
thermodynamic support
replicated samples
negative-memory artifact screen
```

### Language rule

```text
Before complete evidence: candidate.
After complete evidence and replication: phase.
```

---

## Card 5 — FFWT-HAC-CVCD phase detection

### Claim

Multiscale CVCD invariants detect phase changes or material classes better than baseline descriptors.

### Inputs

```text
Raman
XRD
IR
Z(omega)
R(T)
chi(T)
synthetic spectra
```

### Baselines

```text
raw peak features
Fourier features
ordinary wavelets
PCA
classical statistics
simple supervised classifier
```

### Metrics

```text
accuracy
F1
calibration
noise robustness
cross-sample generalization
feature count
interpretability
```

### Falsifiers

```text
no_baseline_improvement
noise_instability
preprocessing_leakage
uninterpretable_invariants
```

---

## Card 6 — Negative-memory artifact bank

### Objective

Turn every failed claim into a reusable anti-error detector.

### Entry format

```text
id: false_positive_contact_short
symptoms:
  - apparent_zero_resistance
  - no_meissner_signal
  - strong_mounting_dependence
blocked_claims:
  - superconductivity
recommended_tests:
  - 4_probe_measurement
  - remount_contacts
  - magnetic_screening
```

### OAK role

A candidate close to known artifacts is not discarded automatically, but it cannot be promoted until the artifact-specific tests are passed.
