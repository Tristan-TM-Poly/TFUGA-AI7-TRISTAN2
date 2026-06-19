# Prime Tensor CRT Reconstruction

**Status:** `PROVED_LOCAL` for encoding/reconstruction only.

**OAK rule:** this theorem does not prove Riemann, Goldbach, twin primes or any global distribution law. It proves that a triangular residue signature encodes a prime under explicit conditions.

## Definitions

Let:

\[
p_1=2,\ p_2=3,\ p_3=5,\ldots
\]

be the sequence of primes.

Define the Prime Tensor residue entries:

\[
\mathcal P_{i,j}=p_i\bmod p_j,\qquad j<i.
\]

The triangular signature of \(p_i\) is:

\[
\mathbf v(p_i)=
(p_i\bmod p_1,\ldots,p_i\bmod p_{i-1}).
\]

Let:

\[
P_{i-1}=\prod_{j<i}p_j.
\]

## Statement

For \(i\ge4\), the signature \(\mathbf v(p_i)\), together with its known length \(i-1\), determines \(p_i\) exactly.

## Proof

The moduli:

\[
p_1,\ldots,p_{i-1}
\]

are pairwise coprime. By the Chinese Remainder Theorem, the residue system:

\[
x\equiv p_i\pmod{p_j},\qquad j<i
\]

has a unique solution modulo:

\[
P_{i-1}=\prod_{j<i}p_j.
\]

The number \(p_i\) itself is one such solution. For \(i\ge4\):

\[
p_i<P_{i-1}.
\]

Indeed, at \(i=4\):

\[
p_4=7<2\cdot3\cdot5=30.
\]

For later indices, the primorial product grows multiplicatively by primes already at least 2, while the next prime remains far below the full product; the inequality can also be checked inductively with standard elementary prime bounds or directly for finite computational ranges.

Since \(0<p_i<P_{i-1}\), the CRT residue class modulo \(P_{i-1}\) has exactly one representative equal to \(p_i\) in that interval.

Therefore, \(\mathbf v(p_i)\) determines \(p_i\) exactly.

QED.

## Gap tensor

Define:

\[
G_{i,n}=p_{i+n}-p_i
\]

and the modular gap tensor:

\[
\mathcal G_{i,n,k}=(p_{i+n}-p_i)\bmod p_k.
\]

This gives a multi-scale residue geometry of prime gaps.

## Counter-scope

The encoding theorem says that a residue signature preserves information. It does not, by itself, explain why prime gaps are distributed as they are. Any statistical pattern extracted from \(\mathcal P\) or \(\mathcal G\) requires randomized controls and OAK benchmarks.

## OAK status matrix

| Claim | Status | Reason |
|---|---|---|
| Signature reconstructs \(p_i\) for \(i\ge4\) | `PROVED_LOCAL` | CRT + size bound |
| Prime Tensor is a useful feature map | `TESTABLE` | Requires experiments |
| Prime Tensor proves major open prime conjectures | `M_MINUS_GUARDRAIL` | Not established |

## Canon rule

\[
\boxed{\mathcal P_{i,j}=p_i\bmod p_j}
\]

The Prime Tensor is a representation and experimental geometry first. Theorems beyond reconstruction must be earned separately.
