# Ω-ROOTFLOW-T∞ R0.8 — Realified & local versal multiplicity strata

## Status

R0.8 extends merged R0.7 without claiming a new theorem. It turns the
multiplicity-stratum constraint matrix into two additional computational
objects:

1. a **real-parameter tangent model** when coefficients are constrained to
   remain real;
2. a **translation-normalized local unfolding compiler** for transverse
   coefficient perturbations.

The mathematical identities are established local calculus. Numerical ranks,
RREF bases, pseudo-inverse decompositions and truncated unfolding roots are
software computations and retain OAK status.

---

## 1. Starting point: the R0.7 multiplicity stratum

For an exact multiplicity-`m` root `c`,

\[
P(c)=P'(c)=\cdots=P^{(m-1)}(c)=0,\qquad P^{(m)}(c)\neq0.
\]

For selected coefficient directions `z^{k_j}`, R0.7 uses

\[
A_{qj}=(k_j)_q c^{k_j-q},\qquad q=0,\ldots,m-2.
\]

Complex coefficient increments tangent to the multiplicity stratum satisfy

\[
A\,d\theta=0.
\]

R0.8 keeps this object and changes the parameter field or the interpretation of
its row space.

---

## 2. Real coefficient constraints

If the allowed coefficient increments are real, `v in R^p`, the condition

\[
A v=0
\]

is equivalent to

\[
\begin{bmatrix}
\Re A\\
\Im A
\end{bmatrix}v=0.
\]

This matters whenever the critical root is non-real.

### Canonical regression

For

\[
P(z)=(z^2+1)^2
\]

and the double root `c=i`, varying all five real coefficients gives

\[
A=[1,i,-1,-i,1].
\]

The realified constraint matrix is

\[
A_R=
\begin{bmatrix}
1&0&-1&0&1\\
0&1&0&-1&0
\end{bmatrix}.
\]

Therefore the local complex constraint rank is `1`, while the real coefficient
codimension is `2`.

R0.8 reports both values explicitly.

For unconstrained complex parameters `theta=x+iy`, R0.8 also provides the
standard block realification

\[
\begin{bmatrix}
\Re A&-\Im A\\
\Im A& \Re A
\end{bmatrix}
\begin{bmatrix}x\\y\end{bmatrix}=0.
\]

---

## 3. Translation-normalized local unfolding

Write

\[
y=z-c,
\qquad
\alpha_m=\frac{P^{(m)}(c)}{m!}.
\]

For a first-order coefficient perturbation `dtheta`, the local Taylor jet is

\[
\delta P(c+y)
=
\sum_{q\ge0}
\left[
\sum_j \binom{k_j}{q}c^{k_j-q}d\theta_j
\right]y^q.
\]

The `y^{m-1}` term is the first-order translation/root-motion direction already
handled by R0.7. After quotienting that direction, the transverse local model is

\[
\boxed{
y^m+\sum_{q=0}^{m-2}u_qy^q
}
\]

with

\[
\boxed{
u_q=
\frac{1}{\alpha_m}
\sum_j\binom{k_j}{q}c^{k_j-q}d\theta_j.
}
\]

R0.8 compiles the linear map

\[
d\theta\mapsto(u_0,\ldots,u_{m-2}).
\]

Its rank measures how many independent first-order local splitting modes are
reachable by the selected coefficient family.

The implementation uses the cautious software labels:

- `OAK_PASS_COMPLETE_LOCAL_UNFOLDING` if the jet rank is `m-1`;
- `OAK_PASS_PARTIAL_LOCAL_UNFOLDING` otherwise.

"Complete" here means complete for this finite, translation-normalized local
jet representation. It is not promoted to a blanket singularity-theory claim
outside the declared model.

---

## 4. Tangent versus transverse coefficient motion

Given an arbitrary selected coefficient direction `dtheta`, R0.8 computes

\[
u=J_{\rm unfold}d\theta.
\]

Using a Moore-Penrose decomposition it returns

\[
d\theta=d\theta_{\parallel}+d\theta_{\perp},
\]

where

\[
J_{\rm unfold}d\theta_{\parallel}\approx0
\]

and `dtheta_perp` is the minimum-norm component reproducing the local splitting
jet.

This produces a practical classifier:

- tangent direction: multiplicity preserved to first order, requiring higher
  order corrections to remain exactly on the stratum;
- transverse direction: multiplicity is split already in the first-order local
  normal model.

---

## 5. Puiseux signature from the first active jet

If the first non-zero local jet term occurs at order `q`, the leading truncated
balance is

\[
y^m+\varepsilon u_q y^q=0
\]

or

\[
y^q\left(y^{m-q}+\varepsilon u_q\right)=0.
\]

Therefore the non-stationary local branches have canonical scale

\[
\boxed{|y|\sim\varepsilon^{1/(m-q)}}.
\]

R0.8 records:

- `first_active_jet_order = q`;
- `predicted_puiseux_exponent = 1/(m-q)`;
- `local_factor_order = q`;
- `splitting_branch_count = m-q`.

### Canonical regressions

For `z^3 + epsilon`:

\[
q=0,\qquad \alpha=1/3.
\]

For `z^3 + epsilon z`:

\[
q=1,\qquad \alpha=1/2.
\]

For `z^4 + epsilon z^2`:

\[
q=2,\qquad \alpha=1/2,
\]

with a factor `z^2` retained in the truncated local model.

These canonical polynomial fixtures are exact. For a general analytic path the
same output is a local truncated-model prediction, not a proof of global branch
behavior.

---

## 6. Local model root generator

R0.8 can solve

\[
y^m+\varepsilon\sum_{q=0}^{m-2}u_qy^q=0
\]

and return `z=c+y`.

This creates a bridge

\[
\text{coefficient direction}
\to
\text{local jet}
\to
\text{Puiseux signature}
\to
\text{predicted local root cloud}.
\]

The `z^3+epsilon` regression compares these roots against the direct polynomial
roots and requires numerical agreement.

---

## 7. CLI surfaces

R0.8 adds:

- `real-tangent`
- `unfolding`

Existing R0.1-R0.6 payload schemas remain R0.6, R0.7-native surfaces remain
R0.7, and the two new modes advertise R0.8. Every payload reports
`engine_version=R0.8`.

---

## 8. OAK boundary

R0.8 does **not** claim:

- a new classification theorem for polynomial singularities;
- that a first-order tangent direction is an exact finite path on the
  multiplicity stratum;
- that a truncated local unfolding predicts all global roots;
- that complex and real coefficient codimensions are interchangeable;
- that a pseudo-inverse decomposition is canonical under every possible metric;
- that finite numerical rank establishes symbolic rank in ill-conditioned
  cases.

R0.8 does provide an executable, testable bridge between coefficient geometry,
real constraints, multiplicity strata, local unfolding modes and Puiseux
scaling.
