# R12 — CVCD constraint atlas for the R10 Hankel criterion

Status: `EXACT_FINITE_ATLAS`, `STRUCTURAL_COMPRESSION`, `NOT_A_RH_PROOF`.

R12 turns the R10 all-orders criterion into a finite, addressable atlas of
proof obligations. For every requested Hankel size `N` and shift, it enumerates
all nonempty principal minors, compiles each one exactly in normalized Theta
coefficients, translates it to an integer polynomial in central xi derivatives,
and fingerprints the normalized polynomial to merge algebraically identical
constraints.

## Raw family

For one `N x N` Hankel matrix there are

\[
2^N-1
\]

nonempty principal minors. With both R10 families (basic and shifted), the raw
number up to maximum size `M` is

\[
2\sum_{N=1}^{M}(2^N-1).
\]

These are finite PSD obligations only. R10 still requires the corresponding
conditions for every size.

## CVCD compression

Each normalized-Theta polynomial is serialized canonically as exact rational
coefficients plus monomial exponent vectors and hashed by SHA-256. Identical
polynomials share one canonical node with multiple occurrence coordinates

`(full_size, shift, principal_indices)`.

For example, through `N=2` and shifts 0,1 there are 8 raw occurrences but only
6 unique polynomials. The constraints `p1` and `p2` reappear as principal
1x1 minors inside the larger Hankel matrices and are therefore deduplicated.

This is a concrete CVCD operation:

\[
\text{many syntactic obligations}
\rightarrow
\text{canonical invariant polynomial}
\rightarrow
\text{all provenance coordinates}.
\]

## Dual representation

Every unique atlas node stores both

1. the sparse polynomial in normalized coefficients `a_j`; and
2. its sign-equivalent integer polynomial in
   `d_(2j)=xi^(2j)(1/2)` after clearing the positive denominator.

Thus one constraint can be consumed by TensorProdLift, exact rational algebra,
interval arithmetic, a CAS, or a future formal prover without changing its
identity.

## Research uses

The atlas enables controlled large-scale generation rather than unstructured
expansion. Candidate uses include redundancy measurement, implication search,
low-degree inequality mining, interval-certification prioritization,
TensorProdLift linear separation, HGFM dependency linking, and Bayes-Tristan
ranking by cost versus discriminatory power.

The fingerprint is algebraic-syntactic after exact expansion. R12 does not yet
identify two different polynomials that are logically equivalent under other
known constraints; that stronger quotient is a future CVCD layer.

## OAK boundary

Deduplicating or satisfying any finite atlas does not establish all-orders R10
positivity. A constraint atlas is a proof-obligation compiler and compression
surface, not a proof of RH.

Run:

```bash
python -m omega_zeta_square_t.r12_cli --max-size 3 --shifts 0 1
```

The dependency-free implementation is capped at size 5 because symbolic
determinant expansion is combinatorial. That cap is an engineering constraint,
not a mathematical bound.
