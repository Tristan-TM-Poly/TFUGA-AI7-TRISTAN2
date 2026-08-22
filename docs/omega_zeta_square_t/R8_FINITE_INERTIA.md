# R8 — Finite atomic inertia theorem

Status: `PROVED_FINITE_ATOMIC_THEOREM`, `NOT_A_FULL_RIEMANN_THEOREM`.

## Statement

Let a finite reciprocal spectral support contain

- \(q\) distinct positive real atoms \(r_1,\ldots,r_q\), and
- \(m\) distinct non-real conjugate pairs \(z_\ell=a_\ell+ib_\ell\), \(\bar z_\ell\), with \(b_\ell\ne0\).

Let

\[
N=q+2m,
\qquad
p_k=\sum_j\lambda_j^k,
\]

and form the full-support Hankel matrix

\[
H_N=(p_{i+j+1})_{i,j=0}^{N-1}.
\]

Then the real symmetric quadratic form associated with \(H_N\) has inertia

\[
\boxed{(n_+,n_-,n_0)=(q+m,m,0)}.
\]

In particular, every non-real conjugate pair contributes exactly one negative
direction. Therefore the finite full-support moment matrix is PSD if and only if
there are no non-real pairs in this support model.

## Proof by real evaluation coordinates

For a real coefficient vector \(c=(c_0,\dots,c_{N-1})\), define

\[
P(x)=\sum_{j=0}^{N-1}c_jx^j.
\]

Then

\[
c^TH_Nc
=\sum_j\lambda_j P(\lambda_j)^2.
\]

The real evaluation map

\[
P\mapsto
\big(P(r_1),\dots,P(r_q),
\Re P(z_1),\Im P(z_1),\dots,
\Re P(z_m),\Im P(z_m)\big)
\]

is an isomorphism from the \(N\)-dimensional real polynomial space of degree
less than \(N\) to \(\mathbb R^N\). Indeed, a polynomial in its kernel vanishes
at all \(N\) distinct complex support points and must therefore be zero.

A positive real atom contributes

\[
r_jP(r_j)^2,
\]

which is a positive one-dimensional block.

For one conjugate pair, write

\[
P(z)=x+iy,
\qquad z=a+ib.
\]

Its combined real contribution is

\[
\begin{aligned}
zP(z)^2+\bar zP(\bar z)^2
&=2\Re\big((a+ib)(x+iy)^2\big)\\
&=2\big(a(x^2-y^2)-2bxy\big).
\end{aligned}
\]

This is the quadratic form of

\[
2\begin{pmatrix}a&-b\\-b&-a\end{pmatrix}.
\]

Its eigenvalues are

\[
\pm2\sqrt{a^2+b^2},
\]

so every genuinely non-real conjugate pair contributes inertia \((1,1,0)\).
By Sylvester's law of inertia, the original Hankel form has the sum of these
block inertias, namely \((q+m,m,0)\).

## Determinant parity

As a corollary,

\[
\operatorname{sgn}\det H_N=(-1)^m.
\]

Thus an odd number of non-real pairs makes the full determinant negative, while
an even number may leave the determinant positive even though the matrix is
still indefinite. This is why **PSD testing is stronger than determinant-sign
testing**.

The synthetic test in the repository includes one positive real atom and two
non-real pairs: its full determinant is positive, but an exact principal-minor
PSD certificate still rejects the matrix.

## OAK boundary

R8 concerns finite support. It does not by itself imply that a finite principal
Hankel matrix built from the full infinite Riemann reciprocal spectrum must be
indefinite whenever one transformed zero is non-real. That requires either:

1. a rigorous infinite-tail stability/witness argument, or
2. completion of the all-orders Stieltjes/analytic-continuation bridge R7.

The finite inertia theorem is therefore a proved local structural result and a
strong adversarial model, not a proof of RH.
