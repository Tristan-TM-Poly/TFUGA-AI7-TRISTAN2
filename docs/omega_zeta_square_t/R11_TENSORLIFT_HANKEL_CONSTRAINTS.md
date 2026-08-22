# R11 — TensorProdLift compiler for R10 Hankel constraints

Status: `EXACT_FINITE_CONSTRAINT_COMPILER`, `R10_DERIVED`, `NOT_A_RH_PROOF`.

R10 converts RH into all-orders positivity of two Hankel families. R11 converts
each **finite** determinant condition into an exact polynomial inequality in the
central Taylor coefficients of the centered-square Riemann function, then views
that polynomial as a linear form in a monomial TensorProdLift space.

## 1. Central coefficients

Write

\[
A(u)=\frac{\Theta(u)}{\Theta(0)}
=1+a_1u+a_2u^2+a_3u^3+\cdots,
\]

where

\[
\boxed{
a_j=\frac{\xi^{(2j)}(1/2)}{(2j)!\,\xi(1/2)}.
}
\]

If the reciprocal spectral coordinates are \(\lambda_n=-1/u_n\), then formally
and, by R10, analytically in a neighborhood of zero,

\[
A(u)=\prod_n(1+\lambda_nu).
\]

Thus the \(a_j\) are elementary symmetric functions of the \(\lambda_n\).

## 2. Newton compiler

Define

\[
p_k=\sum_n\lambda_n^k.
\]

Newton identities give

\[
\begin{aligned}
p_1&=a_1,\\
p_2&=a_1^2-2a_2,\\
p_3&=a_1^3-3a_1a_2+3a_3,\\
p_4&=a_1^4-4a_1^2a_2+2a_2^2+4a_1a_3-4a_4.
\end{aligned}
\]

The R10 Stieltjes moments are \(m_k=p_{k+1}\).

## 3. First all-orders obligations made finite

The first basic and shifted size-one conditions are

\[
\boxed{a_1\ge0}
\]

and

\[
\boxed{a_1^2-2a_2\ge0}.
\]

The first nontrivial basic size-two determinant is

\[
\begin{aligned}
\Delta_{2,0}
&=p_1p_3-p_2^2\\
&=\boxed{a_1^2a_2+3a_1a_3-4a_2^2}.
\end{aligned}
\]

Hence R10 requires

\[
\boxed{a_1^2a_2+3a_1a_3-4a_2^2\ge0}.
\]

The shifted size-two determinant is

\[
\boxed{
\begin{aligned}
\Delta_{2,1}={}&
-2a_1^3a_3+a_1^2a_2^2-4a_1^2a_4
+10a_1a_2a_3\\
&-4a_2^3+8a_2a_4-9a_3^2.
\end{aligned}}
\]

Again, RH would require \(\Delta_{2,1}\ge0\).

## 4. Direct xi-derivative inequality

Let

\[
d_{2j}=\xi^{(2j)}(1/2),
\qquad d_0=\xi(1/2).
\]

Substituting the normalized coefficients into \(\Delta_{2,0}\) gives

\[
\Delta_{2,0}
=
\frac{
3d_0d_2d_6-10d_0d_4^2+15d_2^2d_4
}{1440d_0^3}.
\]

Since \(d_0>0\), the corresponding finite R10 obligation is

\[
\boxed{
3\xi(1/2)\xi''(1/2)\xi^{(6)}(1/2)
-10\xi(1/2)\xi^{(4)}(1/2)^2
+15\xi''(1/2)^2\xi^{(4)}(1/2)
\ge0.
}
\]

This is an equivalent **finite necessary condition** under R10, not an
all-orders proof.

## 5. TensorProdLift interpretation

For \(\Delta_{2,0}\), introduce the lifted feature vector

\[
\Phi(a)=
\begin{pmatrix}
a_1^2a_2\\
a_1a_3\\
a_2^2
\end{pmatrix}.
\]

Then

\[
\boxed{
\Delta_{2,0}=
\begin{pmatrix}1&3&-4\end{pmatrix}\Phi(a).
}
\]

So a nonlinear Hankel determinant in the original coefficient coordinates is a
linear half-space constraint in the lifted monomial coordinates. This is the
precise, OAK-safe role of TensorProdLift-T here.

The compiler generalizes this automatically: for each requested Hankel size and
shift it emits a sparse list

\[
\{(c_\alpha,\alpha)\}
\]

such that

\[
\det H_N^{(s)}
=\sum_\alpha c_\alpha a^\alpha.
\]

## 6. Why this is useful

R11 creates several new research surfaces:

- exact symbolic proof obligations from central derivatives only;
- sparse TensorProdLift features suitable for CVCD redundancy compression;
- interval propagation directly onto polynomial inequalities;
- automated search for low-degree consequences of R10;
- formal-proof targets where each determinant identity can be checked independently;
- comparison against Jensen/Turán/Laguerre inequalities to detect redundancy or stronger constraints.

## 7. Complexity and OAK boundary

The dependency-free compiler intentionally caps symbolic determinants at size 5
because the permutation and polynomial expansions grow combinatorially. This is
an engineering bound, not a mathematical one; larger sizes should use fraction-
free symbolic linear algebra, determinant recurrences, modular reconstruction,
or dedicated CAS/formal tooling.

Generating a polynomial constraint does **not** prove it is nonnegative for the
Riemann coefficients. R11 compiles R10 obligations; it does not discharge them.

OAK status:

`exact identity -> PROMOTE`

`finite necessary inequality -> PROMOTE_AS_OBLIGATION`

`all-orders positivity -> OPEN`

`RH solved -> FALSE`.
