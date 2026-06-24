# CVCD Weak Conservation Theorem

**Status:** `PROVED_LOCAL`

**OAK rule:** this theorem controls observables only when a metric, a reconstruction map and a Lipschitz bound are explicit. It does not certify that every compression is useful.

## Setup

Let \((X,d_X)\) be a metric space. Let:

\[
L:X\to Z
\]

be a compression/log map and:

\[
E:Z\to X
\]

be a decompression/expansion map.

Define the reconstruction residual:

\[
R(x)=d_X(x,E(L(x))).
\]

Let:

\[
f:X\to\mathbb R
\]

be a \(K\)-Lipschitz observable:

\[
|f(x)-f(y)|\le Kd_X(x,y)\quad\forall x,y\in X.
\]

## Statement

For all \(x\in X\):

\[
|f(x)-f(E(L(x)))|\le K R(x).
\]

## Proof

Start from the Lipschitz property with:

\[
y=E(L(x)).
\]

Then:

\[
|f(x)-f(E(L(x)))|
\le
K d_X(x,E(L(x))).
\]

By definition:

\[
R(x)=d_X(x,E(L(x))).
\]

Therefore:

\[
|f(x)-f(E(L(x)))|\le K R(x).
\]

QED.

## Interpretation

If a LOG/EXP pair reconstructs an object with small residual, then every stable observable changes by at most a controlled amount.

This is a precise mathematical seed for CVCD:

\[
X\xrightarrow{L}Z\xrightarrow{E}\hat X\quad\text{with}\quad R(x)=d_X(x,\hat X).
\]

## Minimal finite example

Let \(X=\mathbb R\), \(d_X(x,y)=|x-y|\), \(L(x)=\mathrm{round}(x)\), and \(E(z)=z\). Then:

\[
R(x)=|x-\mathrm{round}(x)|.
\]

For \(f(x)=2x\), \(K=2\). Therefore:

\[
|2x-2\mathrm{round}(x)|\le2|x-\mathrm{round}(x)|.
\]

Equality holds here.

## Counter-scope

If \(f\) is not Lipschitz on the relevant domain, the theorem does not apply. If \(R(x)\) is large, the theorem gives a weak bound. If \(d_X\) is poorly chosen, the residual may not correspond to the scientific quantity of interest.

## OAK status matrix

| Claim | Status | Reason |
|---|---|---|
| Lipschitz residual bound | `PROVED_LOCAL` | Direct proof |
| All compression preserves all meaning | `REJECTED_OVERCLAIM` | Only controlled observables are bounded |
| CVCD usefulness on a task | `TESTABLE` | Requires benchmark, baseline and metric |

## Canon rule

\[
\boxed{|f(x)-f(E(L(x)))|\le K d_X(x,E(L(x)))}
\]

Residual is not decoration. Residual is the price paid by compression.
