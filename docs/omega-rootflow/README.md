# Ω-ROOTFLOW-T∞ — Differential Polynomial Root Flow

Ω-ROOTFLOW-T∞ turns polynomial root finding into a **local differential and continuation problem in coefficient space**.

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

## R0.1 executable surface

- exact first-order root Jacobian with respect to every coefficient;
- simultaneous coefficient-flow velocity `dr/dt = J da/dt`;
- representation-independent differential for arbitrary basis functions `phi_k`;
- analytic coefficient Hessian of every simple root;
- sensitivity to activating a new term `epsilon z^m`;
- projective scaling invariant `J a = 0`;
- residual, `|P'(r)|`, and reciprocal-derivative conditioning diagnostics;
- predictor–corrector continuation in coefficient space;
- deterministic root branch matching;
- finite-difference OAK check of the analytic Jacobian;
- claim-safe JSON CLI.

Coefficient order is always ascending `[a0,a1,...,an]`.

## Geometry and discriminant

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

while multiplicity `m` generically produces a Puiseux exponent `1/m`. R0.1 detects loss of simple-root conditioning; explicit Puiseux continuation through the discriminant is a future extension.

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

If `m` exceeds the original degree, extra roots may enter from infinity as `epsilon -> 0`. R0.1 computes the finite-root sensitivity; homogeneous/projective root-at-infinity tracking is reserved for a later wave.

## Example: `z^3 - 3z + t`

The critical points satisfy `P_z=3z^2-3=0`, hence `z=±1`, and the critical parameter values are `t=±2`. Tracking from `t=0` to `t=1` stays away from the discriminant:

```bash
python -m omega_rootflow_t.cli continue \
  --start '0,-3,0,1' \
  --end '1,-3,0,1' \
  --steps 20
```

Analyze one polynomial:

```bash
python -m omega_rootflow_t.cli analyze --coeffs '0.5,-1,0.2,1'
```

## OAK boundaries

R0.1 distinguishes:

1. **Exact identities for simple roots** — the implicit-differentiation formulas above.
2. **Numerical software checks** — root finding, branch matching, Newton correction and finite-difference agreement.
3. **Research extensions** — optimal global branch tracking through discriminants, monodromy, projective roots at infinity, adaptive basis selection, coefficient-space geodesics and large-degree multi-scale compression.

The CLI reports `theorem_claimed=false` and `scientific_validation_claimed=false`; a passing OAK software fixture is not a new theorem.

## Next waves

- R0.2 adaptive step size from `min |P'(r)|` and predictor residual;
- R0.3 companion-matrix eigenvalue-flow cross-check;
- R0.4 Chebyshev/Legendre/Bernstein adapters and conditioning atlas;
- R0.5 Puiseux local collision models and monodromy loops;
- R0.6 homogeneous/projective roots including infinity;
- R0.7 inverse root design `d a = J^+ d r*`;
- R0.8 uncertainty propagation / Bayes-Tristan;
- R0.9 CVCD/FFWT compression of large spectral root clouds.
