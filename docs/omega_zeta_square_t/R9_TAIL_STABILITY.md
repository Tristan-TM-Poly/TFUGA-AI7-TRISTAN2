# R9 — Rigorous finite-to-infinite tail stability bound

Status: `PROVED_CONDITIONAL_BOUND`, `ANALYTIC_TAIL_INPUTS_REQUIRED`, `NOT_A_RH_PROOF`.

R9 supplies a rigorous bridge from a finite negative Hankel witness to the full
infinite moment matrix **provided** certified bounds on the omitted reciprocal-zero
tail are available.

## Setup

Let \(A\) be a finite real Hankel contribution of size \(N\), and let
\(v=(v_0,\ldots,v_{N-1})\in\mathbb R^N\). Define

\[
P_v(z)=\sum_{i=0}^{N-1}v_i z^i.
\]

Suppose

\[
v^TAv=-\eta<0.
\]

Let the omitted spectral tail consist of reciprocal-zero atoms \(\lambda_j\),
closed under conjugation so that the total Hankel contribution is real. No RH
assumption on the tail is needed for the estimate below.

Assume certified bounds

\[
|\lambda_j|\le R,
\qquad
\sum_{j\in\mathrm{tail}}|\lambda_j|\le M.
\]

## Tail bound

The tail quadratic contribution is

\[
v^TEv
=\sum_{j\in\mathrm{tail}}
\lambda_jP_v(\lambda_j)^2.
\]

Therefore

\[
\begin{aligned}
|v^TEv|
&\le
\sum_j |\lambda_j|\,|P_v(\lambda_j)|^2\\
&\le
M\left(\sum_{i=0}^{N-1}|v_i|R^i\right)^2.
\end{aligned}
\]

Define

\[
B_v(R)=\sum_i|v_i|R^i.
\]

If

\[
\boxed{M B_v(R)^2<\eta},
\]

then

\[
v^T(A+E)v
\le -\eta+MB_v(R)^2<0.
\]

Hence the complete infinite Hankel matrix has a finite negative quadratic
witness and is not PSD.

## Why this matters

Unlike a positivity-tail argument, R9 does not require the omitted atoms to be
positive real. It only needs **absolute** reciprocal-zero bounds. This makes it
compatible with adversarial off-line tails.

The remaining Riemann-specific problem is to produce certified explicit bounds
for

\[
R\ge\sup_{j\in\mathrm{tail}}|\lambda_j|,
\qquad
M\ge\sum_{j\in\mathrm{tail}}|\lambda_j|,
\qquad
\lambda_j=-1/u_j.
\]

The order \(1/2\) of \(\Theta\) strongly motivates absolute summability of the
reciprocal zero images, but a usable R9 proof certificate requires explicit
analytic tail estimates, not only convergence in principle.

## Exact 2x2 witness helper

For

\[
A=\begin{pmatrix}a&b\\b&c\end{pmatrix},
\qquad a>0,
\qquad ac-b^2<0,
\]

the rational vector

\[
v=(-b,a)
\]

satisfies

\[
v^TAv=a(ac-b^2)<0.
\]

This gives a dependency-free exact witness whenever a negative \(2\times2\)
determinant is available with positive first diagonal entry.

## OAK boundary

`tail_stability_certificate` is rigorous only conditional on its supplied tail
bounds. A guessed, numerically sampled, or RH-dependent value of \(R\) or \(M\)
must not be relabeled as an unconditional analytic bound.

R9 therefore decomposes the global problem into two independently auditable
objects:

1. an exact finite negative witness; and
2. a certified analytic tail bound small enough to preserve it.
