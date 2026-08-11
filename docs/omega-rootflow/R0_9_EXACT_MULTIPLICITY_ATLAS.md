# Ω-ROOTFLOW-T∞ R0.9 — Exact global multiplicity atlas

## Status

R0.9 extends the local multiplicity geometry of R0.7/R0.8 to a global exact
multiplicity description for rational-coefficient polynomials.

No numerical root solver is needed for the R0.9 atlas.

The implementation intentionally uses the derivative-gcd tower and exact
square-free decomposition instead of introducing a convention-sensitive
subresultant implementation without a dedicated formal specification.

---

## 1. Derivative-gcd tower

For

\[
P(z)=a_n\prod_i(z-r_i)^{m_i},
\]

define

\[
G_q=\gcd(P,P',\ldots,P^{(q)}),\qquad q=0,\ldots,n.
\]

Over characteristic zero,

\[
\boxed{
\deg G_q=\sum_i\max(m_i-q,0)
}
\]

where the sum runs over distinct complex roots.

Therefore

\[
\boxed{
N_{\ge q}=\deg G_{q-1}-\deg G_q
}
\]

is the number of distinct complex roots with multiplicity at least `q`, and

\[
\boxed{
N_{=q}=N_{\ge q}-N_{\ge q+1}
}
\]

is the number with multiplicity exactly `q`.

This reconstructs the multiplicity partition without explicitly solving for
any root.

---

## 2. Canonical mixed fixture

R0.9 uses

\[
P(z)=(z-1)^3(z+2)^2(z^2+1).
\]

Its degree is 7 and its complex root multiplicities are

\[
\boxed{(3,2,1,1)}.
\]

The derivative-gcd degree tower is

\[
\boxed{(7,3,1,0,0,0,0,0)}.
\]

Thus

\[
N_{\ge1}=4,\qquad N_{\ge2}=2,\qquad N_{\ge3}=1,
\]

and

\[
N_{=1}=2,\qquad N_{=2}=1,\qquad N_{=3}=1.
\]

The complex stratum codimension in the full monic coefficient space is

\[
\boxed{
\sum_i(m_i-1)=n-r=7-4=3.
}
\]

R0.9 reports this complex codimension. Real coefficient strata may have
additional conjugacy structure; R0.8 is the appropriate local realification
layer for those questions.

---

## 3. Exact square-free decomposition

R0.9 performs an exact characteristic-zero gcd decomposition over `Fraction`.
For the canonical fixture it returns the monic factors

\[
z^2+1\quad(m=1),
\]

\[
z+2\quad(m=2),
\]

\[
z-1\quad(m=3).
\]

The original leading coefficient is stored separately and exact reconstruction
is an OAK gate:

\[
a_n\prod_s Q_s(z)^{s}=P(z).
\]

No floating-point tolerance participates in this reconstruction.

---

## 4. Multiplicity partition geometry

A degree-`n` polynomial with distinct root clusters of multiplicities

\[
\lambda=(m_1,\ldots,m_r),\qquad \sum_i m_i=n,
\]

is represented by an integer partition of `n`.

R0.9 uses the local complex codimension

\[
\boxed{
\operatorname{codim}_{\mathbb C}(\lambda)=n-r.
}
\]

Two elementary combinatorial transitions are exposed.

### More singular

Merge two clusters:

\[
(a,b,\ldots)\to(a+b,\ldots).
\]

The number of distinct roots falls by one and the complex codimension rises by
one.

### Less singular

Split one cluster:

\[
(m,\ldots)\to(a,m-a,\ldots).
\]

The number of distinct roots rises by one and the complex codimension falls by
one.

These are combinatorial adjacency relations between multiplicity partitions.
R0.9 does not claim that every physical or constrained parameter family can
realize every edge.

---

## 5. Degree-four lattice regression

For degree 4 the partitions are

\[
(4),\quad(3,1),\quad(2,2),\quad(2,1,1),\quad(1,1,1,1).
\]

The immediate less-to-more-singular edges are

\[
(1,1,1,1)\to(2,1,1),
\]

\[
(2,1,1)\to(3,1),\qquad(2,1,1)\to(2,2),
\]

\[
(3,1)\to(4),\qquad(2,2)\to(4).
\]

R0.9 regression-tests exactly five nodes and five immediate edges.

---

## 6. Optional resource guard

The number of integer partitions grows rapidly. The lattice builder therefore
accepts an optional `maximum_nodes` guard.

There is no mandatory fixed degree ceiling in the API. A caller can leave the
guard unset, or set a workload-specific bound.

This follows the ROOTFLOW/OAK principle that resource constraints should be
explicit rather than silently changing mathematical semantics.

---

## 7. CLI surfaces

R0.9 adds:

- `multiplicity-atlas --coeffs ...`
- `partition-lattice --degree n [--max-nodes N]`

Payload versioning remains cumulative:

- R0.1-R0.6 modes keep payload schema R0.6;
- R0.7-native modes keep R0.7;
- R0.8-native modes keep R0.8;
- the two new modes advertise R0.9;
- all payloads expose `engine_version=R0.9`.

---

## 8. OAK boundary

R0.9 distinguishes:

- exact rational polynomial arithmetic;
- exact gcd-degree multiplicity identities;
- exact square-free decomposition over Q;
- complex multiplicity partitions;
- combinatorial adjacency of partitions;
- real-constrained or application-specific realizability.

A partition edge is not automatically a realizable path in a restricted
physical model. A rational square-free factor may represent several conjugate
or algebraic complex roots. R0.9 reports degree-weighted complex multiplicity
counts and does not pretend to have solved those roots symbolically.
