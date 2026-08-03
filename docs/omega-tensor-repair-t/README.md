# Ω-TENSOR-REPAIR-T∞ / TensorProdLift-T R0.1

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

## Commands

```bash
omega-tensor-repair analyze-2d --left 1 2 --right 3 -1
omega-tensor-repair dimensions 3
omega-tensor-repair compile examples/tensor_repair_spec.json
omega-tensor-repair benchmark --output tensor-oak.json
pytest -q tests/test_omega_tensor_repair_t.py
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

## Block-factorization contract

A `BlockPartition` must cover the complete ambient matrix exactly once. Overlap and uncovered coordinates are rejected. R0.1 provides exact extraction and stitching. CP, Tucker, tensor-train and hierarchical Tucker are explicit future backends rather than falsely advertised features.

Future block-orbit factorization should store one canonical factor core per symmetry orbit plus the transformations needed to reconstruct orbit members.

## OAK boundary

Certification means only that finite executable fixtures satisfy the declared algebraic contracts. It does not establish a new physical law, universal compression superiority, independence of every emitted view, experimental validation, or correctness of unimplemented factorization families.

Every approximate extension must preserve an explicit residual

\[
T=\widehat T+R
\]

and report the norm, provenance and domain of validity of `R`.

## Roadmap

R0.2: basis-explicit irreducible coordinates in arbitrary dimensions, Young symmetrizers, sparse contraction graphs and property-based tests.

R0.3: optional NumPy/SciPy backends for SVD, PSD projection and constrained completion.

R0.4: CP/Tucker/TT/HT adapters, block-orbit shared factors and differentiable projectors behind reconstruction, equivariance, conditioning and uncertainty gates.
