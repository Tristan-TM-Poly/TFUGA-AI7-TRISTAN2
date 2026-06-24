# Omega-PSPT++ Research Roadmap

This roadmap turns the Tristan solid-phase theory into a progressive OAK ladder.

The goal is not to assert a new material phase early. The goal is to build a machine that can generate, simulate, classify, and falsify phase candidates.

---

## Track 1 — Geometry and hyperloop invariants

### Objective

Convert fractal or porous supports into measurable graph invariants.

### Objects

```text
Lambda_n = generated lattice at iteration n
V_n      = occupied sites
E_n      = nearest-neighbor links
c_n      = connected components
beta_1   = |E_n| - |V_n| + c_n
L_T      = sum_k w_k log(1 + |Gamma_k|)
```

### First deliverables

- Cantor product lattice generator.
- Sierpinski carpet generator.
- Menger sponge generator.
- Nearest-neighbor graph construction.
- Cycle-rank/hyperloop score.
- Boundary-site detector.
- ASCII visualization for small lattices.

### OAK promotion

- OAK-1: definitions and graph invariants.
- OAK-2: generated examples and tests.
- OAK-3: prediction that cycle rank or lacunarity explains a response better than porosity alone.

---

## Track 2 — Transport and percolation

### Objective

Test whether geometry changes effective conductance beyond trivial porosity.

### Models

```text
resistor network
random walk diffusion
percolation threshold p_c
contact-normalized effective resistance R_eff
```

### Required controls

- matched porosity;
- matched mass;
- matched bounding box;
- matched contact geometry;
- random porous control;
- non-fractal periodic-hole control.

### Metrics

```text
R_eff, sigma_eff, p_c, conductance anisotropy, robustness to deleted links
```

### Falsifiers

- random porous controls perform equally;
- effect disappears under contact normalization;
- finite-size-only artifact;
- no scaling with iteration depth.

---

## Track 3 — LC/RLC hyperloop response

### Objective

Model fractal loops as coupled resonators.

### Minimal circuit model

```text
omega_gamma = 1 / sqrt(L_gamma C_gamma)
Q_gamma     = (1 / R_gamma) sqrt(L_gamma / C_gamma)
Z_T(omega)  = NetworkImpedance(R, L, C, M)
```

### Deliverables

- loop inventory by scale;
- synthetic impedance spectrum;
- resonance-tree CVCD features;
- loss/Q-factor comparison to controls.

### OAK prediction

```text
If loop hierarchy is physically meaningful, resonance families should scale with iteration depth and not only with total sample size.
```

---

## Track 4 — Tight-binding fractal explorer

### Objective

Use the same lattices as supports for simple Hamiltonians.

### Minimal Hamiltonian

```text
H_ij = -t A_ij + epsilon_i delta_ij
```

### Metrics

```text
E_n, psi_n, DOS(E), IPR_n = sum_i |psi_n(i)|^4
```

### Questions

- Which fractal supports create localization windows?
- Does boundary dimension affect edge/defect modes?
- Does disorder destroy or stabilize specific modes?

---

## Track 5 — Fractal topology detector

### Objective

Move from pretty spectra to topological diagnostics.

### Required ingredients

- spectral gap;
- boundary/corner/defect state maps;
- finite-size scaling;
- disorder robustness;
- real-space topological marker.

### Falsifiers

- dangling-bond modes only;
- no gap;
- topological marker trivial;
- no distinction from trivial Hamiltonian control.

---

## Track 6 — Omega-TFTS candidate simulator

### Objective

Test the strongest candidate in a conservative sequence.

### Minimal model

```text
H_OmegaTFTS = H_frac + H_SOC + H_Z + H_Delta + H_loop + H_dis
```

### Simulation checklist

- BdG spectrum;
- gap candidate;
- boundary/corner/defect modes;
- topological marker;
- robustness to disorder;
- finite-size scaling;
- comparison with trivial control.

### Experimental checklist before any strong claim

- zero resistance or controlled transport evidence;
- Meissner or magnetic screening;
- spectroscopic gap;
- critical current;
- critical field;
- thermodynamic support when possible;
- replication;
- artifact rejection.

---

## Track 7 — FFWT-HAC-CVCD spectroscopy engine

### Objective

Detect phase transitions and material classes from multiscale signatures.

### Inputs

```text
Raman, XRD, IR, impedance, transport, susceptibility, simulated spectra
```

### Features

```text
peaks, widths, shifts, scale coherence, cross-probe coherence, anomaly residues
```

### Baselines

- raw peak tables;
- Fourier/wavelet features;
- PCA/UMAP;
- classical statistics;
- simple supervised model.

### Claim discipline

CVCD is only valuable if it improves prediction, robustness, interpretability, compression, or next-experiment choice.

---

## Track 8 — Bayes-Tristan active measurement

### Objective

Choose the next highest-information test instead of endlessly naming phases.

### Posterior vector

```text
B_T(Phi) = (truth, utility, fertility, testability, safety, profitability, compressibility, replicability)
```

### Decision rule

```text
m* = argmax_m E[Delta OAK | m]
```

### Example

For a superconducting candidate, the next measurement should prioritize:

```text
R(T), chi(T), gap, I_c, B_c, artifact controls
```

not another speculative name.

---

## 90-day build sequence

### Days 1-10

- Finish dependency-free geometry utilities.
- Add graph summaries and cycle-rank tests.
- Add examples for Sierpinski and Menger.

### Days 11-20

- Add resistor-network solver.
- Compare fractal vs random porous controls.
- Store negative-memory cases for contact/porosity artifacts.

### Days 21-35

- Add LC/RLC toy simulator.
- Generate impedance resonance trees.
- Add CVCD feature extraction over synthetic spectra.

### Days 36-50

- Add tight-binding matrix construction.
- Compute eigenvalue spectra using optional NumPy path when available.
- Add IPR and localization descriptors.

### Days 51-65

- Add simple BdG block constructor.
- Add edge/corner mode descriptors.
- Add finite-size scaling diagnostics.

### Days 66-80

- Add phase-card loader/validator.
- Add Bayes-Tristan active next-test recommender.
- Add report generator.

### Days 81-90

- Write first preprint-style technical note.
- Freeze OAK-2 demos.
- Prepare external replication checklist.

---

## Success criteria

The branch is successful if it produces at least one of:

1. a reproducible geometry-to-response simulator;
2. a CVCD feature set that beats simple baselines on phase/material classification;
3. a falsified candidate converted into useful M-minus memory;
4. a new experimentally testable prediction;
5. a controlled demo showing fractal/hyperloop response beyond matched controls.

The branch fails productively if OAK falsifies a strong candidate and records why.
