# Ω-ROOTFLOW-T∞ R0.5 — Vieta / Newton / Resultant Differential Calculus

R0.5 adds an invariant layer between coefficient space and root space.  The goal
is not merely to recompute roots, but to expose exact algebraic quantities that
must remain consistent while roots move under coefficient perturbations.

## 1. Coefficients ↔ elementary symmetric root coordinates

For

\[
P(z)=a_n\prod_{j=1}^n(z-r_j)
\]

and elementary symmetric functions \(e_m\), Vieta gives

\[
e_m(r_1,\ldots,r_n)=(-1)^m\frac{a_{n-m}}{a_n}.
\]

Therefore the Vieta Jacobian is sparse.  In particular

\[
\frac{\partial e_m}{\partial a_{n-m}}=\frac{(-1)^m}{a_n},
\qquad
\frac{\partial e_m}{\partial a_n}=-\frac{e_m}{a_n}.
\]

The projective coefficient direction remains exactly null:

\[
J_{\rm Vieta}\,\mathbf a=0,
\]

because multiplying all coefficients by one common non-zero scalar leaves the
root divisor unchanged.

## 2. Newton sums as compressed spectral coordinates

Define

\[
p_m=\sum_{j=1}^n r_j^m.
\]

R0.5 evaluates these two independent ways:

1. directly from the numerical root spectrum;
2. recursively from normalized polynomial coefficients through Newton's
   identities.

The recurrence continues beyond degree \(n\), which gives a strong regression
surface: a root spectrum and its coefficient representation must agree on an
arbitrarily selected finite sequence of moments, not merely on Vieta's first
\(n\) symmetric coordinates.

## 3. Residue moments and the triangular sensitivity law

For simple roots,

\[
R_q=\sum_j\frac{r_j^q}{P'(r_j)}.
\]

Lagrange interpolation / residue identities give

\[
R_q=0\quad(0\le q\le n-2),
\qquad
R_{n-1}=\frac1{a_n}.
\]

Combining this with

\[
\frac{\partial r_j}{\partial a_k}
=-\frac{r_j^k}{P'(r_j)}
\]

gives

\[
\frac{\partial p_m}{\partial a_k}
=-m\sum_j\frac{r_j^{m-1+k}}{P'(r_j)}.
\]

Hence the universal triangular block

\[
\boxed{
\frac{\partial p_m}{\partial a_k}=0\quad(m+k<n)
}
\]

and its first non-zero diagonal

\[
\boxed{
\frac{\partial p_m}{\partial a_k}=-\frac{m}{a_n}
\quad(m+k=n).
}
\]

This directly answers the motivating question "which root moments begin to
respond when a coefficient \(a_k\) changes?"  Coefficients of lower degree are
invisible to lower spectral power sums until a sharply defined order.

A useful special case is a monic polynomial with only the constant coefficient
shifted by \(t\):

\[
P_t(z)=P(z)+t.
\]

Then

\[
p_1,\ldots,p_{n-1}\text{ are independent of }t,
\qquad
\frac{dp_n}{dt}=-n.
\]

## 4. Resultant and discriminant cross-check

R0.5 constructs the Sylvester matrix and evaluates

\[
\operatorname{Res}(P,Q)=\det S(P,Q).
\]

For \(P\) of degree \(n\),

\[
\operatorname{Disc}(P)
=(-1)^{n(n-1)/2}\frac{\operatorname{Res}(P,P')}{a_n}.
\]

An independent root-product representation is

\[
\operatorname{Disc}(P)
=a_n^{2n-2}\prod_{i<j}(r_i-r_j)^2.
\]

The OAK discriminant audit compares these two numerical pathways.  Close to a
multiple root, both are expected to become ill-conditioned; a small numerical
value is a collision diagnostic, not by itself a symbolic certificate.

## 5. All single-coefficient additions \(P(z)+t z^k\)

Consider

\[
F(z,t)=P(z)+t z^k.
\]

A finite collision satisfies

\[
F(c,t)=0,\qquad F_z(c,t)=0.
\]

For \(k=0\):

\[
P'(c)=0,\qquad t=-P(c).
\]

For \(k>0\) and \(c\ne0\), eliminate \(t\):

\[
\boxed{cP'(c)-kP(c)=0},
\qquad
\boxed{t=-\frac{P(c)}{c^k}}.
\]

Thus every single coefficient direction has its own finite collision atlas.
For \(k=n\), R0.5 separately reports

\[
t=-a_n,
\]

where the leading coefficient vanishes and a branch can move to projective
infinity.  That event belongs to the R0.3/R0.4 projective layer and is not
silently mislabeled as a finite repeated root.

Canonical collision fixture:

\[
P(z)=z^5-5z,
\quad P_t(z)=z^5-5z+t.
\]

The critical points obey \(c^4=1\), so

\[
t=4c,
\qquad t^4=4^4=256.
\]

The four collision parameters therefore form an exact regular four-gon in the
complex parameter plane.

## 6. Second-order parameter kinematics

For a smooth coefficient family \(P(z,t)\), simple-root implicit
differentiation gives

\[
\dot r=-\frac{P_t}{P_z}
\]

and

\[
\boxed{
\ddot r
=-\frac{P_{zz}\dot r^2+2P_{zt}\dot r+P_{tt}}{P_z}.
}
\]

R0.5 exposes both derivatives and local predictors

\[
r(t+\Delta t)\approx r+\dot r\Delta t
\]

and

\[
r(t+\Delta t)\approx
r+\dot r\Delta t+\frac12\ddot r\Delta t^2.
\]

The fixture \(P(z,t)=z^2-t\) at \(t=1\) checks

\[
r=1,\quad \dot r=\frac12,\quad \ddot r=-\frac14
\]

and requires the second-order predictor to improve on the first-order one for a
small finite step.

## 7. CLI

R0.5 adds:

```bash
python -m omega_rootflow_t invariants --coeffs '6,-5,-2,1'
python -m omega_rootflow_t discriminant --coeffs '2,3,4'
python -m omega_rootflow_t collisions --coeffs '0,-5,0,0,0,1' --coefficient-degree 0
python -m omega_rootflow_t kinematics --coeffs=-1,0,1 --velocity=-1,0,0 --delta 0.1
```

All previous commands remain available.

## 8. OAK boundary

R0.5 does not claim a new theorem.  Vieta identities, Newton identities,
residue/Lagrange identities, resultants, discriminants and implicit derivative
formulas are established mathematics.  The implementation contribution is a
composable executable layer that cross-checks these representations and uses
them as constraints for root-flow software.

Distinctions maintained by the code and documentation:

- exact algebraic identity ≠ floating-point proof;
- small discriminant ≠ certified multiplicity without error control;
- local Taylor prediction ≠ global continuation;
- collision candidate from an elimination equation ≠ physical bifurcation in
  an unrelated model;
- projective degree transition ≠ finite repeated root;
- software OAK PASS ≠ scientific validation or mathematical novelty.

## 9. Next high-value wave

R0.6 should combine these invariants with:

- exact/rational arithmetic for integer/rational coefficient fixtures;
- subresultant sequences and multiplicity stratification;
- implicit sensitivities of discriminant and resultant surfaces;
- multi-parameter collision manifolds;
- coefficient-space tangent/null decompositions;
- moment/Hankel compression of large root clouds;
- adaptive representation selection driven jointly by basis conditioning,
  Vieta/Newton residuals and discriminant distance.
