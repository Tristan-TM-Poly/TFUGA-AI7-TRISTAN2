# Ω-TENSOR-REPAIR-T∞ / TensorProdLift-T R0.1–R0.2

## Purpose

This module turns one classical tensor product into a **reconstructible bundle of representations**. It does not redefine the classical law

\[
\dim(V\otimes W)=\dim(V)\dim(W).
\]

Instead, it records the complete tensor, symmetry-adapted projections, retained inputs, block partitions, residuals and OAK evidence in one deterministic object.

For a rank-2 tensor in two dimensions, the exact tree is

\[
4=3+1=(2+1)+1.
\]

The executable orthonormal basis is

\[
q_1=(T_{11}-T_{22})/\sqrt 2,
\quad q_2=(T_{12}+T_{21})/\sqrt 2,
\]

\[
q_3=(T_{11}+T_{22})/\sqrt 2,
\quad q_4=(T_{12}-T_{21})/\sqrt 2.
\]

- `(q1,q2,q3,q4)` is the full 4D tensor channel;
- `(q1,q2,q3)` is the symmetric 3D channel;
- `(q1,q2)` is the symmetric traceless 2D channel;
- `q3` is the scalar trace channel;
- `q4` is the antisymmetric oriented-area channel.

The 4D, 3D, 2D and 1D views are nested or complementary. They are not ten new independent degrees of freedom.

## Implemented R0.1 kernel

- exact `2D × 2D` analysis and synthesis;
- general square decomposition into symmetric-traceless, isotropic and antisymmetric ambient matrices;
- exact dimension identities for arbitrary rank-2 square tensors;
- finite analysis/synthesis frames;
- complete disjoint block partitions and reconstruction;
- finite permutation group averaging;
- iterative dimension-branching tower validation;
- auditable symmetry and trace repairs with explicit correction matrices;
- JSON specification compiler;
- deterministic OAK benchmark over 625 two-vector fixtures;
- standard-library-only Python kernel and Python 3.10–3.13 CI.

## Implemented R0.2 layer

- dense higher-order tensors with arbitrary axis permutations;
- exact full symmetrization and antisymmetrization over selected equal-size axes;
- permutation parity and idempotence checks;
- dimension-level `SU(2)` Clebsch–Gordan branching
  \[
  m\otimes n=(m+n-1)\oplus(m+n-3)\oplus\cdots\oplus(|m-n|+1);
  \]
- pure-Python dominant rank-one extraction and greedy low-rank deflation;
- explicit approximation, residual norm and captured-energy fraction;
- deterministic representation hypergraphs for bundles and symmetry towers;
- 110 focused R0.2 tests in addition to the 25 R0.1 tests;
- an extended deterministic benchmark across 64 `SU(2)` branches and higher-order fixtures.

The `SU(2)` implementation currently certifies the branching dimensions only. It does not claim numerical Clebsch–Gordan coefficients.

The low-rank backend is a deterministic research implementation based on power iteration and deflation. It does not claim the same robustness or optimality guarantees as a production SVD backend.

## Commands

```bash
omega-tensor-repair analyze-2d --left 1 2 --right 3 -1
omega-tensor-repair dimensions 3
omega-tensor-repair su2 3 3
omega-tensor-repair compile examples/tensor_repair_spec.json
omega-tensor-repair benchmark --output tensor-oak-r01.json
omega-tensor-repair benchmark-r02 --output tensor-oak-r02.json
pytest -q tests/test_omega_tensor_repair_t.py tests/test_omega_tensor_repair_t_r02.py
```

## General square identity

For `d ≥ 1`:

\[
V\otimes V = \operatorname{Sym}^2_0(V)\oplus \mathbb{R}I\oplus\Lambda^2(V),
\]

and

\[
d^2=\left(\frac{d(d+1)}2-1\right)+1+\frac{d(d-1)}2.
\]

## Higher-order permutation projectors

For a dense tensor `T` and a selected axis set of size `k`, R0.2 computes

\[
\operatorname{Sym}(T)=\frac{1}{k!}\sum_{\pi\in S_k}P_\pi T,
\]

and

\[
\operatorname{Alt}(T)=\frac{1}{k!}\sum_{\pi\in S_k}\operatorname{sgn}(\pi)P_\pi T.
\]

These operators are exact finite projectors for the represented dense tensor. Their factorial cost means they are intended for small orders in R0.2. Young symmetrizers and sparse permutation plans remain future work.

## Block-factorization contract

A `BlockPartition` must cover the complete ambient matrix exactly once. Overlap and uncovered coordinates are rejected. R0.1 provides exact extraction and stitching. R0.2 adds low-rank matrix factors with an explicit residual, but CP, Tucker, tensor-train and hierarchical Tucker remain future backends rather than falsely advertised features.

Future block-orbit factorization should store one canonical factor core per symmetry orbit plus the transformations needed to reconstruct orbit members.

## Hypergraph contract

Every representation node records at least its dimension, kind and symmetry metadata. Hyperedges retain operations such as `tensor-product`, `projects-to`, `branches-into` and `analysis-synthesis`. The resulting JSON is deterministically hashed for provenance and regression testing.

A hypergraph is an organizational representation, not automatically a mathematical proof or physical truth.

## OAK boundary

Certification means only that finite executable fixtures satisfy the declared algebraic contracts. It does not establish a new physical law, universal compression superiority, independence of every emitted view, experimental validation, or correctness of unimplemented factorization families.

Every approximate extension must preserve an explicit residual

\[
T=\widehat T+R
\]

and report the norm, provenance and domain of validity of `R`.

## Roadmap

R0.3: basis-explicit irreducible coordinates in arbitrary dimensions, Young symmetrizers, sparse contraction graphs, optional NumPy/SciPy SVD and PSD projection.

R0.4: CP/Tucker/TT/HT adapters, block-orbit shared factors, equivariant differentiable projectors and conditioning audits.

R0.5: category-level associators and braidings for repaired bundles, uncertainty propagation and task-adaptive channel routing.
