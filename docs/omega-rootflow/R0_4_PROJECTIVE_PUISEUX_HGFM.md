# Ω-ROOTFLOW-T∞ R0.4 — Projective Flow, Puiseux Diagnostics, Monodromy Groups and Spectral HGFM

R0.4 connects four structures that were separate in R0.1–R0.3:

\[
\boxed{
\text{degree transition}
\rightarrow
\mathbb{CP}^1\text{ root flow}
\rightarrow
\text{collision scaling}
\rightarrow
\text{monodromy group}
\rightarrow
\text{spectral HGFM}
}
\]

The objective is not to hide singularities. It is to change coordinates when affine root coordinates become inappropriate, quantify local branch scaling when collisions occur, record global branch permutations, and compile the resulting trajectory into an auditable hypergraph.

## 1. Projective continuation through degree changes

R0.3 represented a nominal-degree polynomial by its homogenization

\[
F(u,v)=\sum_{k=0}^{n}a_k u^k v^{n-k}.
\]

R0.4 adds sampled path tracking on the projective line. Every sample retains exactly `n` projective roots, even when the effective affine degree falls below `n`.

Two normalized projective roots `[u:v]` and `[u':v']` are matched by chordal distance

\[
d_{\rm ch}=|uv'-vu'|.
\]

This remains bounded as an affine root diverges.

### Exact regression fixture

Use

\[
P_\varepsilon(z)
=(z^2-1)(1+\varepsilon z)
=-1-\varepsilon z+z^2+\varepsilon z^3,
\qquad \varepsilon\downarrow0.
\]

For every `0 < epsilon <= 1/2`, the roots are exactly

\[
-1,\quad +1,\quad -1/\varepsilon.
\]

Thus no finite-root collision occurs: two branches remain fixed while the third tends to projective infinity `[1:0]`. At `epsilon=0`, the nominal cubic divisor is

\[
\{-1,+1,\infty\}.
\]

This separates **degree collapse** from **finite discriminant collision** in the test suite.

CLI:

```bash
python -m omega_rootflow_t projective-flow-demo --samples 33
```

OAK boundary: the R0.4 projective matcher is a sampled metric continuation, not a proof of analytic continuation through arbitrary singular paths.

## 2. Empirical Puiseux exponent diagnostics

Near a branch point, one often expects a local scaling law

\[
|r-r_c|\sim C|t-t_c|^\alpha.
\]

R0.4 fits

\[
\log|r-r_c|
=\log C+\alpha\log|t-t_c|
\]

by least squares on supplied samples. It returns the fitted exponent, prefactor, `R^2`, and a cautious reciprocal-integer pattern detector.

For the canonical fixture

\[
P_t(z)=z^m-t,
\]

the exact local branches satisfy

\[
r_k(t)=t^{1/m}e^{2\pi i k/m},
\]

so

\[
\boxed{\alpha=1/m}.
\]

The regression suite checks `m=2` and `m=3`, expecting exponents `1/2` and `1/3` respectively.

CLI:

```bash
python -m omega_rootflow_t puiseux-demo --multiplicity 3
```

OAK boundary: a numerical exponent near `1/m` is evidence of a local reciprocal pattern in the sampled regime. It is not by itself a proof of algebraic multiplicity or convergence of a complete Puiseux series.

## 3. From monodromy generators to a finite permutation group

R0.3 recovers one permutation from one coefficient loop. R0.4 closes multiple recovered permutations under composition and inversion.

Given generators

\[
\sigma_1,\ldots,\sigma_q\in S_n,
\]

ROOTFLOW enumerates

\[
G=\langle\sigma_1,\ldots,\sigma_q\rangle
\]

under a hard maximum-order resource bound.

It reports:

- group order;
- explicit elements;
- generator cycle decompositions;
- orbit of branch `0`;
- transitivity;
- closure status.

Regression fixtures include:

\[
\langle(12)\rangle\cong C_2
\]

and, on three branches, two adjacent transpositions generating all of

\[
S_3,
\qquad |S_3|=6.
\]

CLI:

```bash
python -m omega_rootflow_t monodromy-group-demo
```

OAK boundary: the group calculation is exact for the supplied discrete permutations, but the claim that a supplied permutation is the true monodromy of a physical or mathematical family still depends on the numerical branch-tracking evidence that generated it.

## 4. Spectral HGFM compiler

R0.4 compiles a projective flow into a JSON-native hypergraph with no graph-database dependency.

### Nodes

Two node types are emitted:

- `coefficient_state`: one coefficient vector / path parameter;
- `projective_root`: one ordered branch in one sample fiber.

### Ordinary edges

- `coefficient_flow`: adjacent coefficient states;
- `root_branch_flow`: the same ordered projective branch between adjacent samples.

Branch edges record chordal displacement and whether the branch entered or left infinity.

### Hyperedges

Each sample creates a `spectrum_fiber` hyperedge containing

\[
\{\text{coefficient state},r_1,\ldots,r_n\}.
\]

This makes the spectral fiber an explicit HGFM object rather than an implicit array relationship.

### Invariants

The compiler records:

- sample count;
- nominal root count;
- constant projective fiber cardinality;
- degree-transition count;
- infinity-transition edge count;
- maximum branch chordal displacement;
- source-flow OAK status.

For `N` samples and nominal degree `n`, the compiled structure contains

\[
N(1+n)
\]

nodes,

\[
(N-1)(1+n)
\]

ordinary flow edges, and `N` spectrum-fiber hyperedges.

The five-sample cubic degree-collapse fixture therefore has exactly 20 nodes, 16 ordinary edges and 5 hyperedges.

CLI:

```bash
python -m omega_rootflow_t hgfm-demo --samples 5
```

The output schema is

```text
omega-rootflow-spectral-hgfm-r0.4
```

and is designed as a bridge to the larger HGFM/CVCD/OAK/Ω-STACK-T∞ architecture.

## 5. R0.4 validation matrix

R0.4 adds targeted tests for:

1. collision-free projective degree flow to one root at infinity;
2. bounded chordal steps while an affine root diverges;
3. canonical double-collision Puiseux exponent `1/2`;
4. canonical triple-collision Puiseux exponent `1/3`;
5. permutation composition, inversion and cycle decomposition;
6. `S3` generation from two transpositions;
7. order-two group generation from square-root monodromy;
8. spectral HGFM node/edge/hyperedge and invariant counts;
9. R0.4 CLI surfaces for projective flow, Puiseux, group and HGFM.

All earlier R0.1–R0.3 numerical and claim-safety tests remain active.

## 6. What is exact, numerical and still open

### Exact/established identities used

- projective homogenization of a polynomial;
- fixed nominal divisor cardinality on `CP^1` when multiplicities are counted;
- canonical `z^m-t` scaling exponent `1/m`;
- finite permutation composition/inversion/group closure;
- combinatorial graph counts from the emitted schema.

### Numerical software layers

- minimum-chordal-distance branch assignment between sampled projective spectra;
- empirical Puiseux exponent fitting;
- numerical monodromy permutations inherited from R0.3 branch tracking;
- compiled HGFM trajectory data.

### Not yet claimed

- certified analytic continuation across arbitrary discriminant singularities;
- automatic proof of a complete Puiseux expansion;
- certified monodromy group for an arbitrary polynomial family from finite sampling;
- optimal path discretization in projective coefficient space;
- scientific validation of an HGFM interpretation beyond its explicit software schema.

All emitted OAK objects retain `theorem_claimed=false` and `scientific_validation_claimed=false` unless a future formally verified layer supplies stronger evidence.

## 7. Next high-value extensions

The next executable frontier is no longer just “more root finding.” It is a global spectral geometry engine:

\[
\boxed{
\text{coefficient manifold}
\rightarrow
\text{discriminant strata}
\rightarrow
\text{projective fibers}
\rightarrow
\text{local Puiseux charts}
\rightarrow
\text{loop generators}
\rightarrow
\text{monodromy group}
\rightarrow
\text{HGFM atlas}
}
\]

Priority future modules:

- automatic discriminant-locus probing and loop synthesis;
- local Puiseux coefficient estimation beyond the leading exponent;
- projective adaptive subdivision driven by chordal curvature;
- monodromy-group generator minimization and orbit decomposition;
- polynomial-matrix/generalized-eigenvalue fibers;
- uncertainty propagation on branch graphs;
- CVCD/FFWT compression of large root trajectories;
- inverse design constrained by monodromy, symmetry and projective topology.
