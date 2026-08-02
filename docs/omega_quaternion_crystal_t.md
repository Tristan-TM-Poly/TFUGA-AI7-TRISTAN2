# Ω-QUATERNION-CRYSTAL-T

Quaternionic 3D operators for crystals, stress, anisotropy, and coupled-field research.

**Status:** executable mathematical prototype. The quaternion and tensor transformations are standard mathematics; material-specific predictions require calibrated constitutive laws, units, boundary conditions, uncertainty, and experimental validation.

## 1. Mother idea

The one-dimensional operators

\[
\exp(b\,\partial_x)f(x)=f(x+b),
\qquad
\exp(\ln(a)\,x\partial_x)f(x)=f(ax)
\]

extend in 3D to translations, rotations, scale changes, stretches, and shears. The OAK-safe representation is not "everything is a quaternion". It is

\[
\boxed{
\text{orientation quaternion}
+\text{affine deformation}
+\text{physical tensors}
+\text{constitutive laws}
+\text{conservation laws}
}
\]

A unit quaternion

\[
q=\cos(\theta/2)+\mathbf n\sin(\theta/2)
\]

rotates a vector encoded as a pure quaternion by

\[
\mathbf v' = q\mathbf v q^{-1}.
\]

A general affine transformation is

\[
\mathbf x' = F\mathbf x+\mathbf b,
\]

and two transformations compose as

\[
(F_2,\mathbf b_2)\circ(F_1,\mathbf b_1)
=
(F_2F_1,F_2\mathbf b_1+\mathbf b_2).
\]

## 2. Mathematical responsibilities

| Object | Responsibility |
|---|---|
| Quaternion `q` | Proper rotation and orientation in 3D |
| Vector `b` | Translation, direction, traction, field component |
| Matrix `F` | General linear map, deformation gradient, stretch, shear |
| Rank-2 tensor | Stress, strain, conductivity, permittivity |
| Rank-3 tensor | Piezoelectric and related couplings |
| Rank-4 tensor | Linear elasticity |
| Scalar/free energy | Thermodynamic state and coupled constitutive response |
| PDE + boundary data | Spatial and temporal physical evolution |

This separation is a canonical anti-bullshit invariant. A quaternion never replaces missing material physics.

## 3. Implemented R0.1 core

The package `omega_quaternion_crystal_t` contains:

- Hamilton quaternion multiplication;
- axis-angle exponentiation;
- normalized 3D vector rotation;
- quaternion-to-rotation-matrix conversion;
- shortest orientation angle with the `q ~ -q` double cover;
- general affine maps `x -> Mx + t`;
- exact affine composition and inversion;
- crystal map `F = R(q) U` for a supplied stretch `U`;
- rank-2 tensor transport `T' = R T R^T`;
- rank-4 elasticity transport;
- cubic elastic constants `(C11, C12, C44)`;
- cubic mechanical-stability margins;
- anisotropic Hooke law `sigma_ij = C_ijkl epsilon_kl`;
- hydrostatic and von Mises stress;
- Schmid resolved shear stress `tau = s . sigma . n`;
- a minimal `CrystalState` and OAK invariant report.

## 4. OAKBench invariants

The deterministic tests verify:

1. a 90-degree rotation about `z` maps `x` to `y`;
2. quaternion rotation preserves vector norm;
3. `q` and `-q` produce the same physical rotation;
4. rotations about different axes do not commute;
5. rank-2 tensor rotation preserves trace and determinant;
6. affine composition follows the semidirect-product law;
7. affine inversion reconstructs the original point;
8. cubic Hooke response and stability inequalities are correct;
9. Schmid projection recovers a prescribed shear stress;
10. `CrystalState` exposes measurable invariants and residuals.

Run:

```bash
python -m pytest tests/test_quaternion_crystal_t.py
python examples/omega_quaternion_crystal_demo.py
omega-quaternion-crystal --axis 0 0 1 --angle-deg 90 --vector 1 0 0
```

## 5. Crystal and stress pipeline

```text
crystal reference frame
    -> orientation quaternion q
    -> rotation matrix R(q)
    -> stretch/shear U
    -> deformation map F = R(q) U
    -> oriented elasticity C(q)
    -> strain epsilon
    -> stress sigma = C(q):epsilon
    -> slip-system projection tau = s.sigma.n
    -> invariants + residues + OAK status
```

For a polycrystal, assign a state to each grain or integration point:

```text
node = {
  position,
  phase,
  orientation q,
  deformation F,
  stress sigma,
  temperature T,
  composition c,
  uncertainty U2,
  provenance
}
```

Interfaces and neighborhoods become HGFM hyperedges. This supports grain-boundary, texture, stress-concentration, and phase-transition studies without confusing a graph relation with a physical law.

## 6. Connections to spectroscopy and FFWT

A future 3D FFWT-HAC-CVCD layer can jointly analyze

\[
q(\mathbf r),\quad
\sigma(\mathbf r),\quad
\varepsilon(\mathbf r),\quad
T(\mathbf r),\quad
I_{Raman}(\mathbf r,\omega).
\]

Candidate observables include:

- orientation misfit across scales;
- quaternion correlation/coherence with sign-equivalence handling;
- stress invariants versus Raman peak shifts and linewidths;
- grain-boundary curvature versus local spectral residuals;
- anisotropic polarization response;
- multi-scale precursors of cracking or phase transformation;
- residual-of-residual maps for model inadequacy.

These are research hypotheses until benchmarked against established EBSD, diffraction, Raman, finite-element, crystal-plasticity, or phase-field baselines.

## 7. Next milestones

### R0.2 — symmetry and texture

- crystallographic point-group symmetry operators;
- minimum disorientation under crystal symmetry;
- Rodrigues vectors and orientation distribution functions;
- EBSD-like orientation maps and grain segmentation;
- symmetry-aware quaternion averaging.

### R0.3 — finite deformation and plasticity

- robust polar decomposition `F = R U`;
- multiplicative decomposition `F = Fe Fp`;
- slip-system libraries for cubic, FCC, BCC, and HCP examples;
- crystal-plasticity update laws;
- accumulated rotation and path-dependent commutator residues.

### R0.4 — multiphysics

- temperature-dependent elasticity and thermal expansion;
- piezoelectric rank-3 tensor transport;
- dielectric, magnetic, optical, and diffusion tensors;
- free-energy derivatives and thermodynamic consistency checks;
- conservation, units, uncertainty, and provenance gates.

### R0.5 — FFWT/HGFM/CVCD

- 3D multi-resolution fields;
- quaternion/tensor covariance and coherence;
- graph and hypergraph neighborhood operators;
- anomaly and crack-initiation benchmarks;
- Raman/FTIR/EBSD/diffraction data adapters.

## 8. Explicit limits

The current module does **not** prove a new physical law. It does not yet implement:

- a material database;
- calibrated units or temperature dependence;
- finite-element assembly;
- plasticity, damage, fracture, or dislocation evolution;
- crystal point-group quotienting;
- experimental validation;
- quantum, optical, electromagnetic, thermal, or chemical field equations.

Its present value is narrower and stronger: it is a tested mathematical kernel for composing 3D transformations and transporting crystal tensors while preserving clear epistemic boundaries.
