# Noether-Tristan — Compression Symmetry Invariant

**Status:** `PROVED_LOCAL`

**OAK rule:** this is an abstract factorization theorem. It is not the physical Noether theorem and does not claim a conserved physical quantity unless a physical action, symmetry and variational structure are provided.

## Statement

Let:

\[
G:X\to X
\]

be a transformation, let:

\[
L:X\to Z
\]

be a compression/projection, and let:

\[
I:X\to Y
\]

be an observable/invariant that factors through \(L\). That is, there exists:

\[
J:Z\to Y
\]

such that:

\[
I=J\circ L.
\]

If \(G\) is invisible after compression:

\[
L(Gx)=L(x)\quad\forall x\in X,
\]

then \(I\) is conserved under \(G\):

\[
I(Gx)=I(x)\quad\forall x\in X.
\]

## Proof

By factorization:

\[
I(Gx)=J(L(Gx)).
\]

By the compression-symmetry hypothesis:

\[
L(Gx)=L(x).
\]

Therefore:

\[
I(Gx)=J(L(x))=I(x).
\]

QED.

## Minimal finite example

Let:

\[
X=\{0,1,2,3\}
\]

and define the compression:

\[
L(x)=x\bmod 2.
\]

Let:

\[
G(x)=x+2\pmod 4.
\]

Then:

\[
L(Gx)=L(x)
\]

because adding 2 preserves parity.

Any invariant depending only on parity, for example:

\[
I(x)=\begin{cases}
E & x\equiv0\pmod2\\
O & x\equiv1\pmod2
\end{cases}
\]

is conserved by \(G\).

## Counter-scope

The theorem says nothing about observables that do not factor through \(L\). If:

\[
I(x)=x,
\]

then \(I(Gx)\neq I(x)\) in general.

## OAK status matrix

| Claim | Status | Reason |
|---|---|---|
| Factorization theorem | `PROVED_LOCAL` | Direct equality proof |
| Physical conservation law | `UNKNOWN` | Requires physical structure |
| Universal invariant generator | `REJECTED_OVERCLAIM` | Only invariants factoring through \(L\) are conserved |

## Canon rule

\[
\boxed{L(Gx)=L(x),\ I=J\circ L\ \Rightarrow\ I(Gx)=I(x)}
\]

A compression symmetry preserves exactly the invariants that live downstream of the compression.
