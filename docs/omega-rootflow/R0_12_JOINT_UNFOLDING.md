# Ω-ROOTFLOW-T∞ R0.12 — Joint multi-cluster unfolding compiler

## Status

R0.12 closes the loop between:

- R0.8 local unfolding of one multiple root;
- R0.9 global multiplicity partitions;
- R0.10 simultaneous mobile cluster geometry;
- R0.11 exact rational confluent geometry.

Its object is the **coupled local split jet** generated at all multiple-root
clusters by one shared coefficient perturbation.

No new theorem or scientific validation is claimed.

---

## 1. One coefficient direction, many local singularities

For a cluster `(c_alpha,m_alpha)`, write

\[
y=z-c_\alpha,
\qquad
\alpha_\alpha=\frac{P^{(m_\alpha)}(c_\alpha)}{m_\alpha!}.
\]

For selected coefficient directions `z^{k_j}`, the translation-normalized local
split jet is

\[
u_{\alpha,q}=
\frac{1}{\alpha_\alpha}
\sum_j\binom{k_j}{q}c_\alpha^{k_j-q}d\theta_j,
\qquad q=0,\ldots,m_\alpha-2.
\]

R0.12 stacks every such row into a global matrix

\[
\boxed{u=J_{joint}d\theta.}
\]

The same coefficient perturbation can therefore split several clusters,
preserve others, or produce different Puiseux regimes at each cluster.

---

## 2. Exact bridge to the mobile stratum matrix

R0.10 uses

\[
A_{\alpha,q,j}=(k_j)_q c_\alpha^{k_j-q}.
\]

Because

\[
(k)_q=q!\binom{k}{q},
\]

R0.12 has row by row

\[
\boxed{
J_{\alpha,q,:}
=\frac{1}{q!\alpha_\alpha}A_{\alpha,q,:}.
}
\]

Since the scale is nonzero at a true multiplicity-`m_alpha` root,

\[
\boxed{\ker J_{joint}=\ker A.}
\]

Thus two interpretations become the same first-order condition:

- zero split jet at every cluster;
- tangent motion along the simultaneous multiplicity stratum.

R0.12 verifies the row scaling and rank agreement numerically as explicit OAK
invariants.

---

## 3. Cluster split signature

For one cluster, suppose the first active joint-jet entry is order `q`.
The truncated local balance is

\[
y^{m_\alpha}+\varepsilon u_{\alpha,q}y^q=0.
\]

Therefore the moving local branches have scale

\[
\boxed{
|y|\sim\varepsilon^{1/(m_\alpha-q)}.
}
\]

R0.12 reports for every cluster:

- first active order;
- predicted Puiseux exponent;
- local factor order;
- number of splitting branches;
- whether the cluster is preserved to first order.

If all cluster jets vanish, the global direction is marked
`OAK_PASS_JOINT_TANGENT_DIRECTION`.

---

## 4. Canonical `(3,2)` fixture

Use

\[
P=(z-1)^3(z+2)^2.
\]

The triple cluster contributes two jet coordinates and the double cluster one,
so

\[
J_{joint}\in\mathbb C^{3\times6}.
\]

Its rank is 3, equal to the R0.10 mobile constraint rank. Therefore both maps
have the same three-dimensional kernel.

Every R0.10 tangent basis vector must produce zero R0.12 joint split jet.

---

## 5. Selective splitting design

R0.12 also solves the inverse linear problem

\[
\boxed{
J_{joint}d\theta=u^*.
}
\]

It uses a minimum-norm least-squares solution numerically.

For real coefficient directions, the complex system is realified before the
solve.

### Target A — split only the triple cluster into three

Choose

\[
u^*=(1,0,0).
\]

Then the triple cluster has first active order `q=0`, hence

\[
\alpha=1/3,
\]

while the double cluster has zero jet and remains first-order preserved.

### Target B — split only two branches from the triple cluster

Choose

\[
u^*=(0,1,0).
\]

The triple cluster begins at `q=1`, so

\[
\alpha=1/2,
\]

with one local factor retained in the truncated model. The double cluster is
preserved.

### Target C — preserve the triple, split the double

Choose

\[
u^*=(0,0,1).
\]

The triple cluster has zero jet while the double cluster has

\[
\alpha=1/2.
\]

These three modes are regression-tested separately.

---

## 6. Reachability is explicit

A restricted coefficient family may not span the desired local jets.

R0.12 therefore returns the actual target residual

\[
\|Jd\theta-u^*\|.
\]

A sufficiently small residual yields
`OAK_PASS_JOINT_UNFOLDING_DESIGN`.

An unreachable target yields
`OAK_WARN_JOINT_UNFOLDING_TARGET_RESIDUAL`.

The solver never converts a least-squares approximation into a statement that
the requested local splitting mode was exactly realized.

---

## 7. ROOTFLOW synthesis after R0.12

The multiplicity branch now composes as

\[
\boxed{
\begin{aligned}
P
&\to \text{exact multiplicity atlas}\\
&\to \text{partition / clusters}\\
&\to \text{mobile confluent constraints}\\
&\to \text{joint local unfolding jets}\\
&\to \text{Puiseux split signatures}\\
&\to \text{selective split/preserve design}\\
&\to \text{local predicted root geometry}.
\end{aligned}}
\]

R0.10 handles numerical cluster placement and fixed Hermite design. R0.11
provides exact rational certification where possible. R0.12 provides the
coupled local control layer.

---

## 8. CLI surfaces

R0.12 adds:

- `joint-unfolding`
- `joint-unfolding-design`

Earlier modes retain their native R0.6-R0.11 payload versions. The two new
modes advertise R0.12 and every payload reports `engine_version=R0.12`.

---

## 9. OAK boundary

R0.12 does **not** claim:

- that a first-order joint jet predicts global root trajectories;
- that every target jet is reachable in every coefficient subspace;
- that numerical rank equals symbolic rank near degeneracy;
- that a least-squares direction is physically realizable in an external
  application;
- that preserving a cluster to first order guarantees exact finite-
  perturbation preservation;
- that a Puiseux exponent from a truncated local balance is a global theorem
  about an arbitrary nonlinear path.

It does provide a tested compiler from shared coefficient perturbations to
coupled local splitting modes, and an inverse solver for selective
split/preserve objectives.
