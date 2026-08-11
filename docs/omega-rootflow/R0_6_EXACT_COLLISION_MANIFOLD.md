# Ω-ROOTFLOW-T∞ R0.6 — Exact Algebra & Collision Manifold Geometry

R0.6 strengthens two weak points of a purely floating-point root-flow engine:

1. exact integer/rational fixtures can now be checked without numerical root
   solving at all;
2. repeated-root events are treated locally as geometric strata in a
   multi-parameter coefficient space rather than only as isolated values along
   one coefficient direction.

## Exact rational layer

`omega_rootflow_t.exact` uses Python `Fraction` throughout and intentionally
rejects binary floating-point inputs. Accepted scalars are integers, rational
strings such as `"7/13"`, and `Fraction` instances.

The layer implements exact polynomial division, Euclidean monic GCD, Sylvester
determinant/resultant, discriminant and Newton power sums.

For

\[
P(z)=(z+2)(z-1)(z-3)=z^3-2z^2-5z+6,
\]

R0.6 checks exactly

\[
\operatorname{Disc}(P)=900,
\qquad \gcd(P,P')=1,
\]

and

\[
(p_0,p_1,p_2,p_3,p_4)=(3,2,14,20,98).
\]

For

\[
Q(z)=(z-1)^2(z+2)=z^3-3z+2,
\]

it checks exactly

\[
\operatorname{Disc}(Q)=0,
\qquad \gcd(Q,Q')=z-1.
\]

These are finite exact arithmetic certificates for the supplied rational
fixtures. They are not a general-purpose symbolic proof engine.

## Why floats are refused in the exact API

`0.1` as a binary float is not exactly the rational number `1/10`. R0.6 does
not silently guess the user's intended rational reconstruction. Use `"1/10"`
when exact rational semantics are intended.

This is an OAK design choice: explicit representation beats hidden conversion.

## Generic double-root collision manifold

Suppose

\[
P(c)=0,\qquad P'(c)=0,\qquad P''(c)\ne0.
\]

Select coefficient directions \(k_1,\ldots,k_m\) and perturb

\[
P(z)\mapsto P(z)+\sum_{j=1}^m\theta_j z^{k_j}.
\]

Differentiating the two collision equations gives

\[
\sum_j c^{k_j}\,d\theta_j=0
\]

and

\[
P''(c)\,dc+
\sum_j k_jc^{k_j-1}\,d\theta_j=0.
\]

Therefore the complex normal to the parameter-space collision stratum is

\[
\boxed{N(c)=(c^{k_1},\ldots,c^{k_m})}
\]

and the complex tangent space is

\[
\boxed{T_c\Delta=\ker N(c)}.
\]

For a tangent vector \(v\), the induced first-order motion of the colliding
root is

\[
\boxed{
 dc(v)=
 -\frac{\sum_j k_j c^{k_j-1}v_j}{P''(c)}.
}
\]

With `m` selected complex coefficient parameters and a nonzero normal, the
local complex tangent dimension is `m-1`.

## Tangent prediction audit

For every computed tangent direction, R0.6 forms

\[
\theta(\varepsilon)=\varepsilon v,
\qquad
c(\varepsilon)=c+\varepsilon dc(v)
\]

and evaluates both collision residuals at finite \(\varepsilon\). Correct
first-order tangent geometry implies

\[
F(c(\varepsilon),\theta(\varepsilon))=O(\varepsilon^2),
\]

\[
F_z(c(\varepsilon),\theta(\varepsilon))=O(\varepsilon^2).
\]

The regression fixture is

\[
Q(z)=z^3-3z+2=(z-1)^2(z+2),
\]

at `c=1`, using coefficient directions `(a0,a1,a2)`. The normal is proportional
to `(1,1,1)`, so the tangent space is two-dimensional over the complex numbers.
Halving epsilon is required to reduce both residual classes approximately by a
factor four.

## Refusal states

The double-root tangent model refuses two important cases:

- the supplied point is not actually on `P=P'=0`;
- `P''(c)` is also zero, signalling multiplicity at least three.

Higher multiplicity needs additional equations

\[
P=P'=\cdots=P^{(m-1)}=0
\]

and belongs to a later stratified-discriminant model rather than being treated
as if it were a generic double collision.

## CLI

```bash
python -m omega_rootflow_t exact-audit \
  --coeffs '2,-3,0,1'

python -m omega_rootflow_t collision-tangent \
  --coeffs '2,-3,0,1' \
  --critical-root 1 \
  --degrees '0,1,2' \
  --epsilon 0.001
```

The shared payload version advances to `R0.6`; all R0.1-R0.5 command semantics
remain covered by regression tests.

## OAK boundary

R0.6 makes exact statements only where exact rational arithmetic supports them.
The complex tangent formulas are standard derivatives of the collision
equations. Finite-epsilon tangent checks remain numerical validation of the
implementation.

In particular:

- exact arithmetic for a fixture is not a proof of a new theorem;
- a numerical tangent basis is not a global parametrization of the
  discriminant;
- generic double-root geometry does not automatically apply to triple or
  higher multiplicities;
- complex parameter tangents differ from a real-constrained parameter problem,
  where real and imaginary constraints must be split explicitly;
- OAK PASS means the declared software invariant passed within its declared
  scope, not scientific validation.

## Next wave

High-value R0.7 directions:

- exact subresultant sequences and multiplicity strata;
- tangent spaces for multiplicity `m>2`;
- real-vs-complex collision manifold dimensions;
- discriminant gradients/Hessians in coefficient space;
- nearest-discriminant optimization and certified safety margins;
- moment/Hankel representations for large root clouds;
- adaptive coordinate selection combining basis condition, discriminant
  distance, exact invariants and projective geometry.
