# Ω-INVERSE-T∞ — executable specification v0.1

## 1. Canonical object

The compiler receives a shifted local series

\[
F(h)=\sum_{n=0}^{N}a_n h^n,
\qquad a_0=0,
\]

representing

\[
F(h)=f(x_0+h)-f(x_0).
\]

The target variable is `z=y-y0`. A regular inverse is represented by

\[
H(z)=\sum_{n=0}^{N}b_nz^n,
\qquad H(0)=0,
\]

with the formal contract

\[
F\circ H=z+O(z^{N+1}),
\qquad H\circ F=h+O(h^{N+1}).
\]

## 2. Invertibility gate

Let

\[
m=\min\{n\ge1:a_n\ne0\}.
\]

The executable state machine is:

- `m=1` -> `regular`: ordinary Taylor reversion;
- `m>1` -> `critical`: Puiseux branch construction;
- no such `m` -> `degenerate`: no inverse is emitted.

For the regular case, the analytic interpretation additionally requires the usual local inverse theorem hypotheses. The formal-series computation itself only requires `a1 != 0`.

## 3. Exact triangular reversion

For

\[
F(h)=a_1h+a_2h^2+\cdots
\]

and

\[
H(z)=b_1z+b_2z^2+\cdots,
\]

`F(H(z))=z` gives

\[
b_1=a_1^{-1}
\]

and, for `n>=2`,

\[
b_n=-\frac1{a_1}\sum_{k=2}^{n}a_k[z^n]H(z)^k.
\]

The reference implementation uses exact rational arithmetic whenever the supplied coefficients are rational.

## 4. Independent formal Newton oracle

The same inverse is computed a second way using

\[
H_{new}=H-\frac{F(H)-z}{F'(H)}.
\]

All divisions are formal power-series divisions. The implementation increases working precision geometrically. Agreement between the triangular and Newton engines is recorded by the core report.

This is an internal cross-check, not an independent proof of analyticity.

## 5. Independent Lagrange-Bürmann oracle

A third coefficient engine is implemented separately in `scripts/omega_inverse_lagrange.py` from

\[
[z^n]H(z)
=\frac1n[h^{n-1}]
\left(\frac{h}{F(h)}\right)^n.
\]

Since

\[
\frac{h}{F(h)}
=
\frac{1}{a_1+a_2h+a_3h^2+\cdots},
\]

the implementation computes one exact reciprocal series and then extracts the required coefficients of its powers.

The Lagrange oracle does not call either reversion implementation. The OAK cross-check is therefore

\[
H_{triangular}=H_{Newton}=H_{Lagrange}
\]

through the requested finite order.

The test suite checks this equality on the named reference families and on a deterministic sweep of 20 rational forward series.

## 6. Inverse jet

If

\[
H(z)=\sum b_nz^n,
\]

then

\[
(f^{-1})^{(n)}(y_0)=n!b_n.
\]

The compiler exports this derivative jet directly. This makes the module usable as a jet transform

\[
J^N_{x_0}f\longmapsto J^N_{y_0}f^{-1}.
\]

## 7. Critical/Puiseux mode

If the first nonzero degree is `m>1`, write

\[
z=t^m,
\qquad h(t)=c_1t+c_2t^2+\cdots.
\]

The leading coefficient satisfies

\[
a_mc_1^m=1.
\]

Therefore there are `m` complex leading branches

\[
c_{1,j}=a_m^{-1/m}e^{2\pi i j/m}.
\]

At successive orders, `c_k` enters linearly for the first time in degree `m+k-1`, allowing recursive solution. v0.1 computes these coefficients numerically in complex arithmetic for the supplied truncated polynomial.

## 8. Recognition hierarchy

The executable recognizer intentionally separates **candidate generation** from **proof**.

### 8.1 Padé

Construct

\[
R(z)=\frac{P_m(z)}{Q_n(z)}
\]

whose Taylor series matches the requested coefficients through the fitted order.

### 8.2 Exact finite-series rational candidate

A low-degree Padé candidate is promoted to a *finite-series rational candidate* only if additional holdout coefficients also match. It is still not called a proven global identity.

### 8.3 Algebraic relation candidate

Search low-degree relations

\[
P(z,H(z))=0
\]

using rational null-space calculations. The fit equations use only part of the available series; remaining coefficients act as holdout checks.

### 8.4 Coefficient-ratio candidate

Search

\[
\frac{b_{n+1}}{b_n}=\frac{P(n)}{Q(n)}
\]

for low-degree rational polynomials `P,Q` on consecutive nonzero coefficients. This can expose hypergeometric-style structure but is not a general special-function proof engine.

## 9. Critical-value atlas proxy

For the supplied truncated polynomial, solve

\[
F'(h_c)=0
\]

numerically and record

\[
z_c=F(h_c).
\]

The minimum nonzero `|z_c|` is reported as a **critical-value radius proxy**.

It must not be interpreted as an exact convergence radius for the original untruncated function, because inverse-branch singularities can also come from singularities, asymptotic values, branch collisions, or complex structure absent from the truncation.

## 10. OAK validation contract

A regular result must record or be testable against:

- exact left-composition residual coefficients;
- exact right-composition residual coefficients;
- triangular/formal-Newton agreement;
- triangular/Newton/Lagrange exact coefficient agreement in the dedicated oracle suite;
- local absolute condition estimate `1/|a1|`;
- candidate/proof status of every recognition result;
- truncated-polynomial warning on the critical atlas.

A critical result must record:

- multiplicity;
- branch count;
- Puiseux parameterization;
- numerical branch coefficients;
- explicit warning that global branch structure is unresolved.

Agreement of three exact finite-order algorithms is evidence about the implementation and formal coefficients. It is not a substitute for the hypotheses needed to claim analytic convergence or global invertibility.

## 11. What v0.1 does not claim

The prototype does **not** claim:

- global injectivity or surjectivity of `f`;
- a globally single-valued inverse;
- exact convergence radii for arbitrary analytic functions;
- that Padé poles are true singularities;
- that a finite coefficient match proves an algebraic/special-function identity;
- certified complex root isolation;
- asymptotically optimal high-order complexity;
- complete Puiseux/Newton polygon handling for arbitrary implicit algebraic curves;
- multivariate inverse jets yet.

## 12. Architecture

```text
function / Taylor data
        |
        v
  LocalJetNormalizer
        |
        v
  InvertibilityGate
   /      |       \
regular critical degenerate
  |        |
  v        v
Taylor   Puiseux
Reverter Branches
  |
  +--> triangular oracle
  +--> formal Newton oracle
  +--> Lagrange-Bürmann oracle
  |        |
  +---+----+
      v
CompositionValidator
      |
      v
Series2Analytic
  | Padé
  | rational candidate
  | algebraic candidate
  | coefficient recurrence/ratio
      |
      v
CriticalAtlas / future BranchTracker
      |
      v
OAK report + M-minus
```

## 13. Integration targets

Ω-INVERSE-T∞ is designed to connect to:

- Ω-LIN-T: inverse maps of local nonlinear models and coordinate transforms;
- Ω-RPU-T∞: select Taylor/Puiseux/Padé/implicit representations by task and region;
- TensorProdLift-T / Carleman-style lifting: compare nonlinear inverse jets with lifted linear operator representations;
- CVCD: compress a forward local jet into an inverse decoder representation while preserving residual evidence;
- Ω-STACK-T∞: route `INVERT` intentions to the appropriate regular, critical, symbolic, numeric, or branch-aware pipeline;
- Formal Proof: convert discovered rational/algebraic identities into proof obligations instead of treating recognition as proof.

## 14. v0.2 research backlog

1. Bell/Faà di Bruno direct inverse-derivative generator as a fourth oracle.
2. FFT/NTT-backed multiplication and faster high-order formal composition/reversion.
3. Symbolic expression front-end with exact derivatives at `x0`.
4. Interval/ball arithmetic certification.
5. Newton-polygon Puiseux support for general implicit relations.
6. Predictor-corrector branch continuation and monodromy experiments.
7. Multivariate inverse jets and implicit systems.
8. D-finite/P-recursive guessing with strict training/holdout separation.
9. Proof-export interface for identities that survive recognition and OAK tests.
10. Scaling benchmarks comparing the three current exact coefficient engines before selecting adaptive high-order routing.
