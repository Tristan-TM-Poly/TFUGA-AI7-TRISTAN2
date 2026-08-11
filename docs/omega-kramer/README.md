# Ω-DET-ADJ-KRAMER-COMPILER-T∞ — R0.1

**Status:** D-MVP candidate  
**Scope:** exact small/medium rational matrices, structural experiments, symbolic-architecture research  
**OAK rule:** no claim of universal superiority over LU/QR/Bareiss; established determinant/adjugate identities remain classical.

## Mother architecture

\[
A
\rightarrow
\text{subset determinant DAG}
\rightarrow
\det(A)
\rightarrow
\text{reverse AD}
\rightarrow
\operatorname{adj}(A)
\rightarrow
\operatorname{adj}(A)b
\rightarrow
x
\rightarrow
\text{certificate}
\]

R0.1 turns the earlier "generate once, project many" determinant idea into an executable shared computation graph.

The subset-DAG backend processes rows in order and stores only the selected-column mask. A transition that appends column \(j\) receives the parity of the inversions created by that choice. The exact determinant therefore uses:

\[
2^n \text{ subset states}, \qquad n2^{n-1}\text{ transitions},
\]

rather than explicitly materializing all \(n!\) Leibniz leaves.

This is still exponential. It is a research backend for shared exact structure, not a replacement for polynomial-time dense numerical elimination.

## Adjugate by backprop

The established identity

\[
\frac{\partial \det A}{\partial a_{ij}}=C_{ij}
\]

implies

\[
\nabla_A\det(A)=\operatorname{adj}(A)^T.
\]

R0.1 reverse-differentiates the same subset DAG used for the determinant. Therefore determinant and all first partial derivatives share the forward computation instead of launching \(n^2\) unrelated minor calculations.

An independent cofactor/Bareiss implementation is retained only as an OAK oracle.

## Kramer-Tristan packet

For \(Ax=b\), define

\[
D=\det(A),\qquad N=\operatorname{adj}(A)b.
\]

When \(D\ne0\),

\[
x=\frac{N}{D}.
\]

R0.1 emits the exact certificate

\[
\boxed{AN-Db=0}.
\]

This identity is checked before division and remains meaningful when \(D=0\).

The packet therefore carries determinant, adjugate, numerator vector, solution when unique, ranks of \(A\) and \([A|b]\), singular classification, exact certificate residual, Gaussian cross-check, domain ledger and subset-DAG metrics.

## Bordered generator

R0.1 verifies the classical bordered identity

\[
\boxed{
\det
\begin{pmatrix}
A & b\\
z^T & \alpha
\end{pmatrix}
=
\alpha\det(A)-z^T\operatorname{adj}(A)b.
}
\]

Thus a single determinant generator contains both the common denominator and all Cramer numerators as coefficients.

## Multiple right-hand sides

For \(AX=B\), the shared adjugate is computed once:

\[
N=\operatorname{adj}(A)B,\qquad X=N/\det(A)
\]

when \(A\) is invertible, with matrix certificate

\[
AN-\det(A)B=0.
\]

## Compound-matrix bridge

`compound_matrix(A, k)` emits every \(k\times k\) minor. This gives the executable bridge

\[
A\rightarrow \wedge^k A \rightarrow \text{minor spectrum}
\]

needed for later higher-adjugate, rank, Plücker, exterior-power and determinantal-jet work.

## Exact vs architectural claims

| Layer | R0.1 status |
|---|---|
| determinant identities | established mathematics |
| adjugate as determinant gradient | established mathematics |
| Cramer and bordered determinant identity | established mathematics |
| compound matrices / minors | established mathematics |
| subset-mask determinant DP | algorithmic implementation of classical combinatorics |
| reverse AD on the shared determinant DAG | executable architecture |
| "Kramer-Tristan" | integrated shared-DAG + certificate + domain-ledger workflow |
| performance advantage | **not claimed**; must be benchmarked by matrix family |

The connection to the classical Baur-Strassen principle is conceptual: derivatives of arithmetic circuits can be obtained with constant-factor circuit-size overhead. R0.1 does not claim a new theorem from that fact; it supplies a concrete determinant DAG whose reverse pass is directly inspectable.

## Complexity boundary

For the subset backend:

\[
S(n)=2^n,\qquad E(n)=n2^{n-1},\qquad L(n)=n!.
\]

This can be dramatically smaller than explicit Leibniz expansion for moderate \(n\), but it is still exponential and eventually loses to polynomial-time elimination.

Future adaptive routing should choose among subset-DAG + reverse AD, Bareiss/fraction-free elimination, Berkowitz, LU/QR, sparse elimination, block Schur complements, low-rank determinant lemmas and Kronecker/symmetry reductions.

## CLI

```bash
python scripts/omega_kramer_tristan.py demo
```

```bash
python scripts/omega_kramer_tristan.py solve \
  --matrix '[[2,1,0],[1,3,1],[0,1,2]]' \
  --rhs '[1,2,3]'
```

The output serializes exact rationals as strings.

## Validation matrix

R0.1 regression tests cover:

1. subset-DAG determinant vs exact Bareiss on deterministic random integer matrices;
2. reverse-AD adjugate vs independent cofactor oracle;
3. \(A\operatorname{adj}(A)=\det(A)I\), including singular matrices;
4. exact Kramer solution and Gaussian cross-check;
5. bordered generator identity;
6. singular consistent/inconsistent classification without unsafe division;
7. multiple right-hand sides with one shared adjugate;
8. compound-matrix endpoint invariants;
9. exact \(2^n\) state and \(n2^{n-1}\) transition counts.

## R0.2 frontier

Highest-value next extensions:

- actual arithmetic-circuit IR with hash-consing and common-subexpression elimination;
- symbolic polynomial/rational nodes and factor-aware domain ledger;
- higher reverse derivatives / determinantal jet;
- higher adjugates from open-index contractions;
- adaptive backend selector using predicted DAG size, fill-in and expression swell;
- Schur/low-rank/Kronecker structure miners;
- benchmark families: random dense, sparse, Vandermonde, Toeplitz, block, low-rank updates, repeated symbolic parameters;
- CVCD cross-representation comparison against LU, Bareiss, Berkowitz and direct minors;
- M⁻ registry for cases where simplification increases expression swell or destroys domain information.

## OAK stop conditions

Do **not** promote R0.1 to a generally faster solver unless benchmarks establish a bounded matrix family where it wins on a declared metric.

Do **not** simplify cancelled determinant factors without retaining their original zero set in the domain ledger.

Do **not** infer a unique solution from a simplified rational expression when the original matrix has \(\det(A)=0\).

Do **not** call the architectural combination a new determinant theorem.
