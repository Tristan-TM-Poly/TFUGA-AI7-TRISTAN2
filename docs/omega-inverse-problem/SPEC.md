# Ω-INVERSE-PROBLEM-T∞ — executable specification R0.1

## 1. Problem object

An inverse problem is represented by

\[
\mathfrak P=(F, X, Y, y_{obs}, C, U, B),
\]

where `F` is the forward map, `C` constraints/priors, `U` uncertainty assumptions, and `B` branch/domain metadata.

R0.1 implements a small dense numerical subset of this architecture.

## 2. Structural gate

For linear `F(x)=Ax`, compute the singular spectrum and numerical rank `r`.

The router classifies:

- `m=n=r`: square full-rank;
- `m>n=r`: overdetermined identifiable in the column space;
- `n>m=r`: underdetermined with state-space nullity `n-r`;
- `r<min(m,n)`: rank-deficient;
- noise/explicit regularization: stabilized inverse route.

The gate must execute before a uniqueness statement.

## 3. Moore–Penrose backend

Using the eigendecomposition

\[
A^TA=V\Lambda V^T,
\]

R0.1 constructs

\[
(A^TA)^+=V\Lambda^+V^T,
\qquad
A^+=(A^TA)^+A^T.
\]

Eigenvalues below the singular-value tolerance are mapped to zero.

The implementation is deliberately reference-grade and stdlib-only; it is not a performance substitute for LAPACK/SVD.

## 4. Regularized backend

For scalar Tikhonov weight `lambda >= 0` and optional prior center `x_p`, solve

\[
\min_x\|Ax-y\|_2^2+\lambda\|x-x_p\|_2^2.
\]

For `lambda>0`,

\[
(A^TA+\lambda I)x=A^Ty+\lambda x_p.
\]

For `lambda=0`, use Moore–Penrose instead of blindly inverting `A^TA`.

## 5. Local nonlinear backend

Given current `x_k`, estimate `J_k` by centered finite differences and solve

\[
\Delta x_k=\arg\min_\Delta\|J_k\Delta-(y-F(x_k))\|^2+\lambda\|\Delta\|^2.
\]

Then apply residual-decreasing backtracking before accepting the step.

Termination is based on residual and step norms. Convergence is local evidence only.

## 6. Bayesian backend

For declared linear-Gaussian assumptions,

\[
x\sim\mathcal N(\mu_0,C_0),
\quad
y|x\sim\mathcal N(Ax,R),
\]

compute

\[
C_{post}=(C_0^{-1}+A^TR^{-1}A)^{-1},
\]

\[
\mu_{post}=C_{post}(C_0^{-1}\mu_0+A^TR^{-1}y).
\]

R0.1 requires invertible `C0` and `R`.

## 7. Identifiability semantics

A small forward residual does not establish unique recovery.

The report therefore exposes:

- rank;
- nullity;
- left nullity;
- singular values;
- condition number on the retained nonzero singular subspace;
- explicit warnings when nullity is nonzero.

Future versions should export a null-space basis and resolution matrix.

## 8. Cycle-consistency semantics

For a reference state `x`, compute

\[
y=Ax,
\quad
\hat x=A^+y,
\quad
\hat y=A\hat x.
\]

Report both

\[
R_I=\|\hat x-x\|_2,
\qquad
R_F=\|\hat y-y\|_2.
\]

`R_F≈0` with `R_I>0` can be the correct result for a state containing null-space components.

## 9. Router contract

R0.1 linear routing rules:

```text
if noise_level > 0 or lambda > 0:
    TIKHONOV
elif rank < min(m,n):
    MOORE_PENROSE + rank-deficiency warning
elif m == n:
    DIRECT_OR_MOORE_PENROSE
elif m > n:
    LEAST_SQUARES_MOORE_PENROSE
else:
    MINIMUM_NORM_MOORE_PENROSE
```

Future routing adds:

- Ω-INVERSE-T∞ Taylor/Puiseux backend;
- constrained optimization;
- sparse/robust backends;
- nonlinear Bayesian backend;
- multimodal branch ensemble.

## 10. OAK failure conditions

The implementation must fail promotion if any of these occur:

1. underdetermined reference case is described as uniquely recovered;
2. rank-deficient case hides nullity;
3. regularized solution is described as more truthful merely because it is smoother;
4. Bayesian posterior is described without its prior/noise assumptions;
5. nonlinear solver increases residual without rejection;
6. deterministic reference tests disagree with closed-form cases;
7. large-scale numerical superiority is claimed without recognized-library baselines.

## 11. Integration graph

```text
Ω-LIN-T --------------------+
                            |
Ω-INVERSE-T∞ -> local jet --+--> Ω-INVERSE-PROBLEM-T∞
                            |       |
Bayes-Tristan --------------+       +--> identification
                                    +--> inverse design
CVCD -------------------------------+--> decode/reconstruct
                                    +--> control inversion
OAK --------------------------------+--> evidence / failure gates
```

R0.1 implements only the bounded numerical kernel needed to make this architecture executable and testable.
