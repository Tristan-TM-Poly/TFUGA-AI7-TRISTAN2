# R13 — Zero-count envelope → reciprocal-zero tail compiler

Status: `PROVED_CONDITIONAL_TRANSFORM`, `SOURCE_CONSTANTS_NOT_HARDCODED`, `NOT_A_RH_PROOF`.

R13 turns any independently certified explicit upper envelope for the positive-
ordinate zero-counting function into the two analytic inputs required by R9.

## 1. Reciprocal centered-square magnitude

For a nontrivial zero

\[
\rho=\beta+i\gamma,
\qquad
u=(\rho-\tfrac12)^2,
\qquad
\lambda=-1/u,
\]

we have exactly

\[
|u|=(\beta-\tfrac12)^2+\gamma^2
\]

and therefore, without RH,

\[
\boxed{
|\lambda|
=\frac1{(\beta-\tfrac12)^2+\gamma^2}
\le\frac1{\gamma^2}.
}
\]

Thus every transformed zero above height `T` satisfies

\[
\boxed{|\lambda|\le T^{-2}}.
\]

This gives the R9 radius bound

\[
R(T)=T^{-2}.
\]

## 2. Compile a zero-counting envelope

Suppose a primary theorem supplies, for `t>=T0`,

\[
N(t)\le a\,t\log t+b\,t+c\log t+d.
\]

Then

\[
\sum_{\gamma>T}|\lambda_\rho|
\le
\sum_{\gamma>T}\gamma^{-2}.
\]

Using Stieltjes integration/summation by parts and discarding the favorable
negative boundary term,

\[
\sum_{\gamma>T}\gamma^{-2}
\le
2\int_T^\infty\frac{N(t)}{t^3}\,dt.
\]

The required elementary integrals are

\[
\int_T^\infty\frac{\log t}{t^2}dt
=\frac{\log T+1}{T},
\]

\[
\int_T^\infty\frac{dt}{t^2}=\frac1T,
\]

\[
\int_T^\infty\frac{\log t}{t^3}dt
=\frac{\log T+1/2}{2T^2},
\]

and

\[
\int_T^\infty\frac{dt}{t^3}=\frac1{2T^2}.
\]

Hence

\[
\boxed{
M(T)
\le
\frac{2a(\log T+1)+2b}{T}
+
\frac{c(\log T+1/2)+d}{T^2}.
}
\]

Together,

\[
\boxed{
R(T)\le T^{-2},
\qquad
\sum_{\gamma>T}|\lambda_\rho|\le M(T).
}
\]

These are exactly the two inputs consumed by the R9 tail-stability theorem.

## 3. Why constants are not hardcoded yet

The code deliberately accepts an explicit `ZeroCountEnvelope` carrying a
`source_id` and a certification flag. This prevents a remembered, rounded,
misquoted, or out-of-domain literature constant from silently becoming an OAK
analytic input.

A source-specific adapter should be added only after checking the exact theorem,
its convention for `N(T)`, its lower-validity threshold, endpoint treatment, and
all numerical constants against the primary text.

An uncertified envelope may be used for exploratory sensitivity calculations,
but its output is labeled

`CONDITIONAL_ON_UNCERTIFIED_ZERO_COUNT_ENVELOPE`

and cannot be consumed as an unconditional R9 certificate.

## 4. R9 composition

Given a finite negative witness

\[
v^TAv=-\eta<0,
\]

R9 + R13 certify survival into the full infinite spectrum whenever

\[
M(T)
\left(
\sum_i|v_i|T^{-2i}
\right)^2
<\eta.
\]

This creates a concrete quantitative optimization problem:

- choose a finite witness;
- choose/truncate at height `T`;
- certify an explicit `N(t)` envelope;
- compile `R(T),M(T)`;
- test the exact residual margin.

## 5. OAK boundary

R13 proves the **transformation from a certified counting envelope to a tail
bound**. It does not certify any particular published envelope by itself and
does not establish RH.

The next source-specific step must bind exact constants and validity ranges to a
primary zero-counting theorem in the bibliography ledger and test them against
the published statement.
