# Ω-ROOTFLOW-T∞ R0.11 — Exact rational confluent-Hermite geometry

## Status

R0.11 is the exact rational counterpart of R0.10.

R0.10 supports arbitrary complex cluster locations numerically. R0.11 restricts
cluster locations and coefficients to rational values and performs all matrix,
nullspace, cluster-velocity and fixed-location Hermite computations with
`fractions.Fraction`.

This restriction is deliberate: exact output is preferred over silently
converting irrational or floating-point input into a false certificate.

---

## 1. Exact confluent evaluation

For rational root `c`, derivative order `q` and monomial degree `k`,

\[
E(c,q,k)=(k)_q c^{k-q}
\]

is a rational number.

R0.11 builds both:

- the mobile matrix with `q=0,...,m-2`;
- the fixed-location Hermite matrix with `q=0,...,m-1`.

No numerical tolerance participates.

---

## 2. Exact RREF and nullspace

R0.11 performs Gaussian/RREF elimination directly in `Fraction` arithmetic.

It returns:

- exact pivot columns;
- exact rank;
- exact nullspace basis;
- exact consistency for augmented affine systems.

For a mobile tangent basis vector `v`, the invariant

\[
A v=0
\]

is checked by exact equality to zero.

The basis is deterministic: every free coordinate is activated once and pivot
coordinates are solved from RREF. It is not normalized with an irrational
Euclidean norm.

---

## 3. Exact `(3,2)` mobile stratum

Use

\[
P(z)=(z-1)^3(z+2)^2
\]

with ascending coefficients

\[
[-4,8,-1,-5,1,1].
\]

For clusters `(1,3)` and `(-2,2)`, and coefficient degrees `0,...,5`, the exact
mobile matrix is

\[
\begin{bmatrix}
1&1&1&1&1&1\\
0&1&2&3&4&5\\
1&-2&4&-8&16&-32
\end{bmatrix}.
\]

R0.11 certifies

\[
\operatorname{rank}_{\mathbb Q}A=3,
\]

so its rational nullspace has dimension 3.

For each exact tangent basis vector it also computes the two cluster velocities

\[
\dot c_\alpha
=-\frac{E(c_\alpha,m_\alpha-1,\cdot)v}
{P^{(m_\alpha)}(c_\alpha)}
\]

as exact rational numbers.

---

## 4. Exact fixed-location Hermite design

For prescribed rational clusters, the fixed Hermite system is affine-linear in
coefficients.

Given selected free coefficients,

\[
H_{free}\Delta a_{free}=-Ha.
\]

R0.11 solves this system exactly by RREF.

If the system is underdetermined, non-pivot free variables are set to zero.
This is a deterministic exact gauge, **not** a minimum-norm claim.

If the system is inconsistent, R0.11 refuses it.

---

## 5. Exact determinant certificate

For the `(3,2)` fixed-location problem with free degrees `0,...,4` and the monic
coefficient fixed, the Hermite matrix is square and

\[
\boxed{\det H=1458\neq0}.
\]

Therefore the five free coefficients are uniquely determined over Q.

Starting from `z^5`, R0.11 recovers exactly

\[
\boxed{[-4,8,-1,-5,1,1]}.
\]

The final Hermite residual is exactly zero.

---

## 6. Fractional cluster regression

R0.11 also tests

\[
(z-1/2)^2(z+1/3)
\]

and recovers exact ascending coefficients

\[
\boxed{[1/12,-1/12,-2/3,1]}.
\]

This ensures the layer is genuinely rational rather than merely integer-safe.

---

## 7. Relation to R0.10

The intended split is:

### R0.10

- arbitrary complex cluster positions;
- real or complex coefficient design;
- numerical RREF/least-squares;
- finite residuals and condition-sensitive rank.

### R0.11

- rational cluster positions only;
- rational coefficients only;
- exact RREF and rank;
- exact tangent residuals;
- exact rational velocities;
- exact affine Hermite solve;
- exact determinant when square.

Neither layer replaces the other.

---

## 8. CLI surfaces

R0.11 adds:

- `exact-multi-cluster-tangent`
- `exact-hermite-design`

Exact cluster syntax remains

`rational:multiplicity,rational:multiplicity,...`

for example

`1:3,-2:2`

or

`1/2:2,-1/3:1`.

Complex literals such as `1j` are intentionally rejected by exact surfaces and
remain available through R0.10 numerical commands.

Earlier payload modes preserve their native R0.6-R0.10 versions. The two new
modes advertise R0.11 and every payload reports `engine_version=R0.11`.

---

## 9. OAK boundary

R0.11's exactness applies to:

- supplied rational coefficients;
- supplied rational cluster locations;
- finite rational linear algebra;
- exact polynomial derivative constraints.

It does not imply:

- symbolic certification for arbitrary algebraic/irrational root locations;
- a formal theorem-prover proof of every implementation property;
- minimum-norm optimality of the exact affine solution;
- global integrability of mobile tangent vectors;
- scientific validation of an application using the resulting polynomial.
