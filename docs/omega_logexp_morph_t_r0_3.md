# Ω-LOGEXP-MORPH-T∞² — R0.3

## Hybrid continuous, discrete, singular, and residual morphism codex

**Status:** executable finite-dimensional prototype / OAK-safe / not a universal physical law.

## Central statement

The unsafe claim

```text
Every transformation is directly exp(K).
```

is replaced by the typed representation

```text
T = projection · discrete_sector · singular_sector
    · ordered_product(exp(generator_j)) · lift + residual.
```

For a normalized operator `N_T`, the compressed candidate is

```text
Gamma_T = Compress(Log_branch(N_T)).
```

A logarithm is not automatically a compression, physical explanation, or proof.

## R0.3 executable contributions

### 1. Active factorization

For a real matrix `T` of rank `r`, R0.3 selects independent columns `C`, an
invertible active core `U`, and corresponding rows `R` such that

```text
T = C U^{-1} R = C B.
```

The implementation records:

- pivot rows and columns;
- active rank;
- invertible active core;
- exact reconstruction residual;
- a description-length compression proxy.

This gives singular and rectangular morphisms an explicit active sector instead
of forcing a nonexistent direct logarithm on the full map.

### 2. Polar-log decomposition in 2D

For an invertible real `2x2` matrix with positive determinant:

```text
T = Q U = exp(Omega) exp(E),
```

where:

- `Q` is a proper rotation;
- `U` is symmetric positive definite;
- `Omega` is the rotation generator;
- `E = Log(U)` is the logarithmic strain generator.

This implementation is deliberately restricted to `2x2` and rejects:

- singular maps;
- orientation-reversing maps;
- matrices outside the supported real continuous sector.

### 3. Commutator graph

For named generators `G_i`, R0.3 computes

```text
[G_i, G_j] = G_i G_j - G_j G_i
```

and the normalized interaction score

```text
||[G_i,G_j]||_F / (||G_i||_F ||G_j||_F).
```

A nonzero score proves order sensitivity in the selected representation. It does
not by itself prove a causal physical interaction.

### 4. Tensor composition

R0.3 implements the Kronecker product and Kronecker sum:

```text
K_1 boxplus K_2 = K_1 tensor I + I tensor K_2.
```

For independent square generators this is the generator associated with the
tensor-product evolution.

### 5. Second-order Magnus kernel

For equal piecewise-constant time steps:

```text
Omega_2 = sum_i dt G_i
          + 1/2 sum_{i>j} dt^2 [G_i,G_j].
```

The correction preserves first-order history dependence. Higher Magnus orders,
convergence bounds, adaptive steps, and uncertainty are future work.

### 6. Morph Codex

Every matrix can be classified into a minimal typed record:

```yaml
signature:
  domain_dimension: n
  codomain_dimension: m
  rank: r
  kernel_dimension: n-r
  cokernel_dimension: m-r
  determinant_sign: positive | negative | zero | not_applicable
  invertible: bool
representation: finite-real-matrix
continuous_model: direct-or-product-log-candidate | lifted-or-active-support-factorization
discrete_sector: []
singular_sector: []
branch_ledger: {}
invariants: {}
residuals: {}
uncertainty: {}
validity: {}
status: prototype
```

## OAK distinctions

R0.3 keeps these claims separate:

```text
representable != directly exponentiable
exponentiable != compressed
compressed != interpretable
interpretable != causal
reconstructive != physically validated
```

## Current exactness boundary

Exact within numerical tolerance:

- active rank factorization;
- reconstruction of supported 2D polar-log maps;
- Kronecker product and sum;
- commutator evaluation;
- typed kernel/cokernel dimensions.

Prototype or heuristic:

- compression-gain proxy;
- interpretation of commutator strength;
- zero-valued uncertainty placeholders;
- automatic choice of representation.

Not implemented yet:

- global real or complex matrix logarithm;
- general SVD and polar decomposition in arbitrary dimension;
- branch tracking across trajectories;
- topology and homotopy sectors;
- Koopman/Perron representations;
- quantum, Markov, chemical, or PDE bridges;
- FFWT multi-scale generator compression.

## OAKBench

```bash
python -m pytest \
  tests/test_logexp_morph_t.py \
  tests/test_logexp_morph_t_r0_3.py
```

The R0.3 tests cover:

1. exact rectangular rank-one factorization;
2. exact rank-two factorization;
3. positive-determinant polar-log reconstruction;
4. reflection rejection;
5. commuting versus coupled generators;
6. Kronecker-sum spectrum;
7. Magnus reduction for commuting generators;
8. kernel and cokernel reporting;
9. explicit zero-map singularity.

## Next milestones

### R0.4 — General active spectra

- stable QR and SVD backends;
- logarithms of positive singular values;
- truncated-rank residual curves;
- condition numbers and uncertainty propagation;
- description-length accounting using serialized bytes.

### R0.5 — Lie and history engine

- BCH order selection;
- adaptive Magnus integration;
- closure tests for generator libraries;
- binary and ternary commutator hypergraphs;
- path dependence and holonomy ledgers.

### R0.6 — Crystal bridge

- `SO(3)` and quaternion branch continuity;
- `F = R U` polar-log decomposition in 3D;
- symmetry-reduced crystal orientation sectors;
- logarithmic strain and stress transport;
- coupling to Raman, EBSD, diffraction, temperature, and defects.

## Canonical invariant

The system may grow without an arbitrary conceptual ceiling, but promotion is
strictly earned:

```text
candidate growth can be massive;
canon growth requires type, provenance, reconstruction, residual,
uncertainty, falsification, and domain of validity.
```
