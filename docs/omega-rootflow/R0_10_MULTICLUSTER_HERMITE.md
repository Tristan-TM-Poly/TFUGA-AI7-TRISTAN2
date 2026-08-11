# Ω-ROOTFLOW-T∞ R0.10 — Multi-cluster Hermite geometry

## Status

R0.10 connects the global multiplicity partitions of R0.9 to simultaneous
local geometry at several distinct root clusters.

It deliberately distinguishes two problems:

1. **mobile clusters** — preserve each requested multiplicity while allowing
   the cluster centers to move;
2. **fixed clusters** — impose prescribed root locations and multiplicities by
   linear Hermite constraints on coefficients.

No new theorem is claimed. The underlying derivative constraints are standard
polynomial/Hermite calculus; numerical RREF and least-squares operations remain
software procedures.

---

## 1. Root clusters

A cluster is

\[
(c_\alpha,m_\alpha),
\]

with distinct centers `c_alpha` and positive multiplicities `m_alpha`.

For selected coefficient directions `z^{k_j}`, define the confluent evaluation
entry

\[
E_{\alpha,q,j}=(k_j)_q c_\alpha^{k_j-q}.
\]

This is the derivative of `z^{k_j}` of order `q`, evaluated at the cluster
center.

---

## 2. Mobile multiplicity clusters

If a multiplicity-`m_alpha` root is allowed to move, the first
`m_alpha-1` differentiated constraints contain no root-velocity term because
all lower derivatives of `P` vanish there.

Therefore the mobile-cluster tangent matrix stacks

\[
\boxed{
A_{\alpha,q,j}=(k_j)_q c_\alpha^{k_j-q},
\qquad q=0,\ldots,m_\alpha-2.
}
\]

A simultaneous coefficient direction is tangent iff

\[
\boxed{A\,d\theta=0.}
\]

For each tangent vector, the final constraint gives each cluster velocity

\[
\boxed{
\dot c_\alpha
=-\frac{
\sum_j(k_j)_{m_\alpha-1}c_\alpha^{k_j-m_\alpha+1}d\theta_j
}{P^{(m_\alpha)}(c_\alpha)}.
}
\]

R0.10 computes all cluster velocities simultaneously.

---

## 3. Full coefficient-space codimension

For distinct clusters and the complete coefficient direction set, the expected
complex codimension is

\[
\boxed{
\sum_\alpha(m_\alpha-1).
}
\]

This matches R0.9:

\[
n-r=\sum_i(m_i-1).
\]

R0.10 reports the observed numerical matrix rank and the expected full-space
codimension separately. A restricted parameter family can have a different
rank and must not be silently promoted to the full coefficient geometry.

---

## 4. Canonical `(3,2)` fixture

Use

\[
P(z)=(z-1)^3(z+2)^2
=z^5+z^4-5z^3-z^2+8z-4.
\]

The clusters are

\[
(1,3),\qquad(-2,2).
\]

For coefficient degrees `0,...,5`, the mobile constraint matrix is

\[
\begin{bmatrix}
1&1&1&1&1&1\\
0&1&2&3&4&5\\
1&-2&4&-8&16&-32
\end{bmatrix}.
\]

Its rank is 3, equal to

\[
(3-1)+(2-1)=3.
\]

Thus the six-dimensional coefficient vector space has a three-dimensional
local tangent kernel before projective/gauge choices.

R0.10 perturbs coefficients along every computed tangent basis vector, moves
both cluster centers by their predicted velocities, and checks all vanishing
constraints through the requested multiplicity. The residuals must scale as
`O(epsilon^2)`.

---

## 5. Fixed-location Hermite constraints

If cluster locations are fixed rather than mobile, every derivative through
order `m_alpha-1` must vanish:

\[
\boxed{
P^{(q)}(c_\alpha)=0,
\qquad q=0,\ldots,m_\alpha-1.
}
\]

These conditions are linear in the coefficient vector.

The fixed-cluster Hermite matrix therefore stacks the same confluent rows but
includes the final derivative row that the mobile model uses to compute root
velocity.

For the `(3,2)` fixture, there are exactly five fixed-location constraints.
With the monic leading coefficient held fixed, the remaining five coefficients
are uniquely determined.

Starting from

\[
P_0(z)=z^5,
\]

R0.10 recovers numerically

\[
\boxed{[-4,8,-1,-5,1,1]}
\]

in ascending coefficient order.

---

## 6. Hermite inverse design

Given starting coefficients `a`, selected free degrees and target clusters,
R0.10 solves

\[
H_{\rm free}\,\Delta a_{\rm free}=-H a
\]

with a minimum-norm least-squares solve.

For real coefficient design with complex cluster locations, the complex
constraints are realified:

\[
\begin{bmatrix}
\Re H\\
\Im H
\end{bmatrix}
\Delta a_{\mathbb R}
=
-\begin{bmatrix}
\Re(Ha)\\
\Im(Ha)
\end{bmatrix}.
\]

This allows conjugate root clusters to be imposed while preserving real
coefficients.

### Canonical conjugate regression

Starting from `z^4`, impose double roots at `i` and `-i` with the monic
coefficient fixed. R0.10 must recover

\[
(z^2+1)^2=z^4+2z^2+1.
\]

---

## 7. Relation to earlier ROOTFLOW layers

The intended composition is

\[
\text{R0.9 partition}
\to
\text{R0.10 cluster locations}
\to
\text{confluent constraints}
\to
\begin{cases}
\text{mobile tangent + cluster velocities},\\
\text{fixed Hermite inverse design}
\end{cases}
\to
\text{R0.8 local unfolding if a cluster splits}.
\]

This provides a continuous bridge between global multiplicity structure,
local tangent geometry and controlled splitting.

---

## 8. CLI surfaces

R0.10 adds:

- `multi-cluster-tangent`
- `hermite-design`

Cluster syntax is

`root:multiplicity,root:multiplicity,...`

Examples:

`1:3,-2:2`

and

`1j:2,-1j:2`.

Earlier payload versions remain frozen at their native R0.6-R0.9 schemas. The
two new modes advertise R0.10 and every payload reports
`engine_version=R0.10`.

---

## 9. OAK boundary

R0.10 does **not** claim:

- that every multiplicity partition can be realized by every restricted
  coefficient family;
- that numerical matrix rank is symbolic rank near ill-conditioning;
- that a first-order mobile tangent vector integrates globally without higher
  corrections;
- that a least-squares solution is unique when the free Hermite matrix is rank
  deficient;
- that fixed-location Hermite design solves the harder problem where target
  root positions are themselves unknown.

R0.10 does provide an executable bridge between multiplicity partitions,
confluent evaluation matrices, simultaneous moving clusters and fixed-location
multiple-root coefficient design.
