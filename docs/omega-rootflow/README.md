# Ω-ROOTFLOW-T∞ — Differential Polynomial Root Flow

Ω-ROOTFLOW-T∞ turns polynomial root finding into a **local differential, spectral-geometry, continuation and inverse-design problem in coefficient space**.

For

\[
P(z;\mathbf a)=\sum_{k=0}^{n} a_k z^k,
\qquad P(r_j;\mathbf a)=0,
\]

implicit differentiation gives, for every simple root,

\[
\boxed{dr_j=-\frac{dP(r_j)}{P'(r_j)}}
\]

and therefore

\[
\boxed{\frac{\partial r_j}{\partial a_k}=-\frac{r_j^k}{P'(r_j)}}.
\]

This identity does **not** evade Abel–Ruffini: it is a local analytic sensitivity law for simple roots, not a universal radical formula for degree >= 5.

## R0.1 analytic kernel

- exact first-order root Jacobian with respect to every coefficient;
- simultaneous coefficient-flow velocity `dr/dt = J da/dt`;
- representation-independent differential for arbitrary basis functions `phi_k`;
- analytic coefficient Hessian of every simple root;
- sensitivity to activating a new term `epsilon z^m`;
- projective scaling invariant `J a = 0`;
- residual, `|P'(r)|`, and reciprocal-derivative conditioning diagnostics;
- fixed-step predictor-corrector continuation in coefficient space;
- deterministic root branch matching;
- finite-difference OAK check of the analytic Jacobian;
- claim-safe JSON CLI.

Coefficient order is always ascending `[a0,a1,...,an]`.

## R0.2 spectral / adaptive / inverse layer

R0.2 turns the root list into a coupled spectrum with independent numerical cross-checks and inverse control.

### Companion-matrix representation

For `P(z)=a0+...+an*z^n`, ROOTFLOW constructs the Frobenius companion matrix

\[
C(P)=
\begin{pmatrix}
0&\cdots&0&-a_0/a_n\\
1&\cdots&0&-a_1/a_n\\
 &\ddots& &\vdots\\
0&\cdots&1&-a_{n-1}/a_n
\end{pmatrix},
\]

whose eigenvalues are the polynomial roots. `companion_crosscheck` compares the direct polynomial-root solver with `eig(C)` after branch matching. This is an **independent numerical representation check**, not an additional theorem claim.

### Discriminant geometry

If the roots are `r_i`,

\[
\operatorname{Disc}(P)
=a_n^{2n-2}\prod_{i<j}(r_i-r_j)^2.
\]

R0.2 exposes pairwise separations and computes

\[
\log |\operatorname{Disc}(P)|
=(2n-2)\log|a_n|+2\sum_{i<j}\log|r_i-r_j|,
\]

which is more numerically useful than directly multiplying many small/large factors.

### Adaptive continuation

`continue_roots_adaptive` dynamically changes the coefficient-space step using:

- predictor polynomial residual;
- Newton-corrected residual;
- minimum `|P'(r)|`;
- explicit rejected-step accounting.

The loop is

\[
\boxed{
J\,d\mathbf a
\rightarrow
r_{\rm predicted}
\rightarrow
P(r_{\rm predicted})
\rightarrow
\text{accept/shrink}
\rightarrow
\text{Newton correct}
\rightarrow
\text{OAK branch cross-check}
}
\]

and refuses to silently step through a region where the simple-root coordinates become unresolved at the configured minimum step.

Example near the cubic discriminant at `t=2`:

```bash
python -m omega_rootflow_t adaptive \
  --start '0,-3,0,1' \
  --end '1.99,-3,0,1' \
  --initial-step 0.25 \
  --predictor-tolerance 1e-3
```

### Differential inverse root design

The forward differential is

\[
d\mathbf r = J\,d\mathbf a.
\]

R0.2 solves the local inverse problem

\[
\boxed{d\mathbf a=J^+d\mathbf r^\star}
\]

by least squares. By default the leading coefficient is held fixed, removing the projective scaling null direction.

For real-coefficient designs the complex system is converted into the real stacked system

\[
\begin{pmatrix}
\Re J\\
\Im J
\end{pmatrix}
d\mathbf a
\simeq
\begin{pmatrix}
\Re d\mathbf r^\star\\
\Im d\mathbf r^\star
\end{pmatrix}.
\]

`inverse_design_roots` then repeats this local solve with:

1. trust-radius clipping;
2. nonlinear root recomputation;
3. monotone backtracking line search;
4. deterministic branch matching;
5. explicit convergence/stall status.

Example: start from `z^2-1` and move the spectrum to roots `-1.1, 1.3`:

```bash
python -m omega_rootflow_t inverse-design \
  --coeffs=-1,0,1 \
  --target-roots=-1.1,1.3
```

The exact monic target is

\[
(z+1.1)(z-1.3)=z^2-0.2z-1.43.
\]

This fixture is used as a nonlinear inverse-design regression test.

### Root uncertainty propagation

Given coefficient covariance `Sigma_a`, the local first-order root covariance is

\[
\boxed{\Sigma_r=J\Sigma_aJ^H}.
\]

`propagate_root_covariance` validates Hermitian positive-semidefinite input and returns a Hermitian spectrum covariance. This is explicitly a **local linearized uncertainty model**; it must not be extrapolated across a discriminant as though the root posterior stayed Gaussian.

## Geometry and projective gauge

The coefficient vector is projective: `P` and `lambda P` have identical roots. Consequently the radial coefficient direction is null:

\[
J_{\rm root}\,\mathbf a=0.
\]

The singular set is the polynomial discriminant. A multiple root satisfies

\[
P(r)=P'(r)=0.
\]

As `|P'(r)| -> 0`, the simple-root Jacobian diverges. ROOTFLOW refuses analytic Jacobian evaluation once the configured singularity threshold is crossed rather than silently returning misleading large numbers.

For a generic double collision,

\[
r-r_c\sim C(t-t_c)^{1/2},
\]

while multiplicity `m` generically produces a Puiseux exponent `1/m`. R0.2 detects and adapts to deteriorating simple-root conditioning but does not yet implement Puiseux continuation through a collision.

## Multi-representation differential

If

\[
P(z)=\sum_k a_k\phi_k(z),
\]

then

\[
dr=-\frac{\sum_k\phi_k(r)\,da_k}{P'(r)}.
\]

`basis_root_differential` exposes this directly, so the same root-flow law can be used with monomials, Chebyshev, Legendre, Bernstein, or custom bases when `phi_k(r)` and `P'(r)` are supplied consistently.

## Degree activation

For

\[
P_\epsilon(z)=P(z)+\epsilon z^m,
\]

an existing simple root has

\[
\left.\frac{dr}{d\epsilon}\right|_{\epsilon=0}
=-\frac{r^m}{P'(r)}.
\]

If `m` exceeds the original degree, extra roots may enter from infinity as `epsilon -> 0`. R0.2 computes the finite-root sensitivity; homogeneous/projective root-at-infinity tracking remains a future wave.

## CLI surface

Analyze one polynomial:

```bash
python -m omega_rootflow_t analyze --coeffs '0.5,-1,0.2,1'
```

Run a companion/discriminant cross-check:

```bash
python -m omega_rootflow_t spectral --coeffs '-1,0,1'
```

Fixed-step continuation:

```bash
python -m omega_rootflow_t continue \
  --start '0,-3,0,1' \
  --end '1,-3,0,1' \
  --steps 20
```

Adaptive continuation:

```bash
python -m omega_rootflow_t adaptive \
  --start '0,-3,0,1' \
  --end '1.99,-3,0,1'
```

Inverse design:

```bash
python -m omega_rootflow_t inverse-design \
  --coeffs=-1,0,1 \
  --target-roots=-1.1,1.3
```

## OAK boundaries

ROOTFLOW distinguishes:

1. **Exact identities for simple roots** — implicit differentiation, coefficient Jacobian/Hessian and projective null direction.
2. **Equivalent established representations** — polynomial zeros and Frobenius companion eigenvalues.
3. **Numerical software checks** — root finding, eigenvalue computation, branch matching, Newton correction, finite differences and continuation.
4. **Local models** — covariance propagation and differential inverse design.
5. **Research extensions** — optimal global branch tracking through discriminants, monodromy, projective roots at infinity, adaptive basis selection, coefficient-space geodesics and large-degree multi-scale compression.

Every OAK result keeps `theorem_claimed=false` and `scientific_validation_claimed=false`. A passing software fixture is evidence that the implementation matches its stated identities and numerical baselines in the tested regime; it is not a new theorem.

## Validation matrix

R0.1 tests:

- closed-form quadratic coefficient sensitivity;
- analytic Jacobian vs independent central differences;
- projective null direction;
- arbitrary-basis differential;
- Hessian symmetry / second derivative;
- degree activation;
- fixed-step cubic continuation;
- repeated-root singularity guard;
- claim-safe OAK/CLI payloads.

R0.2 tests add:

- companion eigenvalues vs direct roots;
- quadratic discriminant closed form;
- collision detection;
- covariance Hermitian/PSD preservation;
- gauge-fixed linear inverse solve;
- nonlinear monic quadratic inverse design;
- adaptive step shrinking near the cubic discriminant;
- singular-start refusal;
- spectral and inverse-design CLI commands.

## Next waves

- R0.3 Chebyshev/Legendre/Bernstein conversion adapters plus conditioning atlas;
- R0.4 Puiseux local collision models and monodromy loops;
- R0.5 homogeneous/projective roots including infinity;
- R0.6 continuation and inverse design for parameterized polynomial matrices / generalized eigenproblems;
- R0.7 Bayes-Tristan / UNC² nonlinear Monte Carlo comparison against local covariance;
- R0.8 CVCD/FFWT compression of large spectral root clouds;
- R0.9 HGFM spectral branch graphs across coefficient-space loops and bifurcation surfaces.
