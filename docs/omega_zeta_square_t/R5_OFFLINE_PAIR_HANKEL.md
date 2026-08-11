# R5 — Isolated off-line pair Hankel identity

Status: `PROVED_LOCAL_IDENTITY`, `NOT_A_RH_PROOF`, `NOT_A_FULL_ZERO_SET_THEOREM`.

## Setup

Let

\[
\rho=\frac12+\delta+i\gamma,
\qquad
u=(\rho-\tfrac12)^2=(\delta+i\gamma)^2.
\]

Define the reciprocal spectral coordinate

\[
\lambda=-\frac1u=a+ib.
\]

Under the critical-line condition \(\delta=0\), we have

\[
u=-\gamma^2,
\qquad
\lambda=\gamma^{-2}>0.
\]

An off-line zero with \(\delta\neq0\) gives a non-real \(\lambda\). After the
functional/conjugation symmetries are quotiented by the centered square, the
local non-real contribution occurs as the conjugate pair
\(\lambda,\bar\lambda\).

For the *isolated pair model* define

\[
p_k=\lambda^k+\bar\lambda^k.
\]

The first nontrivial Hankel matrix for the Stieltjes indexing used by the
package is

\[
H_2=\begin{pmatrix}p_1&p_2\\p_2&p_3\end{pmatrix}.
\]

## Exact determinant

For \(\lambda=a+ib\),

\[
\begin{aligned}
p_1&=2a,\\
p_2&=2(a^2-b^2),\\
p_3&=2(a^3-3ab^2).
\end{aligned}
\]

Therefore

\[
\begin{aligned}
\det H_2
&=p_1p_3-p_2^2\\
&=4a(a^3-3ab^2)-4(a^2-b^2)^2\\
&=-4b^2(a^2+b^2).
\end{aligned}
\]

Hence an isolated genuinely non-real conjugate pair has

\[
\boxed{\det H_2<0}.
\]

## Centered-square form

Write

\[
x=\delta^2-\gamma^2,
\qquad
y=2\delta\gamma,
\qquad u=x+iy.
\]

Since

\[
|u|=\delta^2+\gamma^2,
\]

we have

\[
\lambda=-\frac1u
=\frac{-x+iy}{(\delta^2+\gamma^2)^2}.
\]

Thus

\[
b^2=\frac{4\delta^2\gamma^2}{(\delta^2+\gamma^2)^4},
\qquad
a^2+b^2=|\lambda|^2=\frac1{(\delta^2+\gamma^2)^2}.
\]

Substitution gives the exact identity

\[
\boxed{
\det H_2
=-\frac{16\delta^2\gamma^2}{(\delta^2+\gamma^2)^6}
}.
\]

Because \(D_{RH}=\delta^2\), the local negative Hankel signal contains the
centered critical-line defect explicitly.

For a nontrivial zero \(\gamma\neq0\), the isolated-pair determinant is zero
on the critical line and strictly negative off it.

## OAK boundary: other zeros can mask the rank-2 signal

Hankel determinants are nonlinear in the moments, so the isolated-pair result
does **not** imply that the full Riemann moment sequence must fail at rank 2.

A synthetic exact example demonstrates masking. Take spectral atoms

\[
\{5,1+i,1-i\}.
\]

Then

\[
(p_1,p_2,p_3,p_4,p_5,p_6)
=(7,25,121,617,3117,15625).
\]

At rank 2,

\[
\det H_2^{(0)}=222>0,
\qquad
\det H_2^{(1)}=784>0.
\]

The non-real pair is therefore hidden from the two rank-2 determinant tests.
At rank 3, however,

\[
\det H_3^{(0)}=-11560,
\qquad
\det H_3^{(1)}=-115600.
\]

This motivates the research quantity **detection depth**: the smallest Hankel
order at which a non-real spectral component forces a finite Stieltjes
violation after all background contributions are included.

## Research target opened by this lemma

The global target remains unproved:

\[
\text{off-critical Riemann zero}
\stackrel{?}{\Longrightarrow}
\text{finite Hankel/Stieltjes violation at some order}.
\]

R5 proves only the isolated-pair identity and provides exact finite mixture
examples. The next work must control the aggregate contribution of the full
zero set, rather than discarding it.
