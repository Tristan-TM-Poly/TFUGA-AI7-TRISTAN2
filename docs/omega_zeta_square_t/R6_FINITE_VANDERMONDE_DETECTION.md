# R6 — Finite one-pair Vandermonde detection theorem

Status: `PROVED_FINITE_ATOMIC_IDENTITY`, `NOT_A_FULL_RIEMANN_THEOREM`.

## Statement

Let the finite spectral support consist of

\[
r_1,\dots,r_q>0
\]

with distinct real atoms, together with one non-real conjugate pair

\[
z=a+ib,\qquad \bar z=a-ib,\qquad b\ne0.
\]

Let \(N=q+2\) be the support size and define

\[
p_k=\sum_{j=1}^q r_j^k+z^k+\bar z^k,
\qquad k\ge1.
\]

For shift \(s\ge0\), define the full-support Hankel matrix

\[
H_N^{(s)}=(p_{i+j+s+1})_{i,j=0}^{N-1}.
\]

Then

\[
\boxed{\det H_N^{(s)}<0}
\]

for every \(s\ge0\).

Thus a finite atomic model containing exactly one non-real conjugate pair and
otherwise positive real atoms necessarily has a finite Stieltjes/Hankel
violation, even if smaller Hankel orders are positive.

## Vandermonde factorization

Let the complete support be

\[
\lambda_1,\dots,\lambda_N
= r_1,\dots,r_q,z,\bar z.
\]

Set

\[
V_{ij}=\lambda_j^i,
\qquad 0\le i\le N-1.
\]

Then

\[
H_N^{(s)}
=V\,\operatorname{diag}(\lambda_1^{s+1},\dots,\lambda_N^{s+1})V^T,
\]

and therefore

\[
\det H_N^{(s)}
=\left(\prod_j\lambda_j^{s+1}\right)
\left(\prod_{i<j}(\lambda_j-\lambda_i)^2\right).
\]

For \(s=0\), separate the factors.

The support product is

\[
\prod_j\lambda_j
=(a^2+b^2)\prod_j r_j>0.
\]

The internal conjugate-pair Vandermonde factor is

\[
(\bar z-z)^2=(-2ib)^2=-4b^2<0.
\]

Every real-real factor is positive after squaring:

\[
(r_j-r_i)^2>0.
\]

For each positive real atom \(r_j\), the four cross factors between the real
atom and the conjugate pair combine as

\[
(z-r_j)^2(\bar z-r_j)^2
=\big((a-r_j)^2+b^2\big)^2>0.
\]

Hence

\[
\boxed{
\det H_N^{(0)}
=-4b^2(a^2+b^2)
\left(\prod_jr_j\right)
\left(\prod_{i<j}(r_j-r_i)^2\right)
\left(\prod_j((a-r_j)^2+b^2)^2\right)<0.
}
\]

For a shift \(s\),

\[
\det H_N^{(s)}
=\det H_N^{(0)}
\left((a^2+b^2)\prod_jr_j\right)^s,
\]

and the extra factor is positive. Therefore the determinant remains negative.

## Relation to the R5 masking example

For

\[
\{5,1+i,1-i\},
\]

we have \(q=1\), \(N=3\). R5 showed that both rank-2 determinant tests are
positive, but R6 predicts the full-support rank-3 sign exactly:

\[
\det H_3^{(0)}=-11560,
\qquad
\det H_3^{(1)}=-115600.
\]

This explains the masking phenomenon: lower orders may miss the complex pair,
but the full finite support cannot.

## OAK boundary

The nontrivial Riemann spectrum is infinite. R6 does not justify truncating the
infinite set and discarding the tail. A positive real tail can perturb every
finite Hankel matrix.

The next theorem target is therefore not another finite example but a rigorous
bridge such as

\[
\text{finite negative witness} + \text{certified tail bound}
\Longrightarrow
\text{full infinite negative witness}.
\]

An alternative route is to use the classical Stieltjes moment existence theorem
at all orders and analytic continuation of the logarithmic derivative. Both
routes remain separate proof obligations until every convergence, support,
uniqueness, and continuation step is discharged.
