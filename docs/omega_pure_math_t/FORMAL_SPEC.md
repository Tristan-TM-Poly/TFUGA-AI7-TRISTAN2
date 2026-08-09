# Ω-PURE-MATH-T∞ — R0.1 formal specification

## 1. Epistemic contract

Every mathematical object in this module belongs to one of these statuses:

- **definition** — terminology fixed by this repository;
- **proposition/theorem** — statement supplied with a proof basis or direct reduction;
- **conjecture** — open target;
- **heuristic** — useful score or search rule without theorem status;
- **counterexample** — explicit failure witness.

A finite computational check may falsify a universal statement but does not prove
one unless the tested finite domain is itself the complete carrier or a separate
proof establishes completeness.

## 2. Six principles

### P1 — representation relativity

An object and a representation are not identified by default. A theory may keep
a family \(\operatorname{Rep}(X)=\{R_\alpha(X)\}\) and explicit maps between them.

### P2 — invariance and quasi-invariance

For an action \(g\),

\[
D_I(g,x)=d(I(gx),I(x)).
\]

Exact invariance is \(D_I=0\); approximate invariance must state a metric,
normalization and tolerance.

### P3 — defects are objects

For a law \(L=R\), define a defect where subtraction/difference is meaningful:

\[
\Delta=L-R.
\]

Examples include commutators, associators and conservation residuals.

### P4 — relative factorization

Irreducibility is always relative to a language/category and its allowed
operations. Absence of a known factorization is not evidence of irreducibility.

### P5 — fertile compression

The working heuristic

\[
\Phi(T)=\frac{\mathcal K(\operatorname{Closure}(T))}
{1+\mathcal K(T)}
\]

is explicitly non-canonical until the complexity model \(\mathcal K\) and
closure operator are fixed.

### P6 — obstruction before construction

Before searching for a morphism or equivalence, compute cheap preserved
invariants and known obstructions.

## 3. T1 proof skeleton — brick-length subadditivity

Let \((\mathcal C,\otimes,\mathbf1)\) be a monoidal setting with an admissible
brick family \(\mathcal B\). Suppose

\[
X\simeq B_1\otimes\cdots\otimes B_m,
\qquad
Y\simeq C_1\otimes\cdots\otimes C_n
\]

are minimum-length admissible witnesses and composition of witnesses is
admissible. Then

\[
X\otimes Y\simeq
B_1\otimes\cdots\otimes B_m\otimes
C_1\otimes\cdots\otimes C_n
\]

is a witness of length \(m+n\). Since the minimum cannot exceed the length of
this witness,

\[
\ell_{\mathcal B}(X\otimes Y)
\le \ell_{\mathcal B}(X)+\ell_{\mathcal B}(Y).
\]

The Python certificate checks this inequality for explicit witnesses; it does
not infer that the inputs are globally minimal.

## 4. T2 proof skeleton — bracket diameter

Let a binary operation be associative. Every full binary parenthesization of
\(x_1\cdots x_n\) has the same value; this follows by the standard
reassociation theorem/induction. Hence every pairwise metric distance is zero
and therefore \(D_A=0\).

Conversely, for \(n=3\) there are exactly two full parenthesizations,

\[
(xy)z,\qquad x(yz).
\]

If their metric distance is zero for every triple and the metric separates
points, then the two values are equal for every triple, which is associativity.

**Required hypothesis:** the chosen metric must satisfy \(d(a,b)=0\Rightarrow
a=b\). A pseudometric only yields equality modulo its zero-distance relation.

## 5. T3 proof skeleton — invariant obstruction

Let \(I\) be preserved by admissible isomorphisms. If an admissible isomorphism
\(f:X\to Y\) existed, invariance would imply \(I(X)=I(Y)\). Thus
\(I(X)\ne I(Y)\) contradicts existence of \(f\).

The executable API therefore names the method `obstructs_isomorphism` and
documents the preservation assumption instead of pretending to discover it.

## 6. Bracket Spectrum

For an ordered list \(x=(x_1,\ldots,x_n)\), let \(\mathcal P_n\) be the full
binary parenthesizations. Define

\[
E_x:\mathcal P_n\to A
\]

by evaluating the binary operation according to each tree. The finite bracket
spectrum is the image \(E_x(\mathcal P_n)\). Given a metric \(d\),

\[
D_A(x)=
\max_{P,Q\in\mathcal P_n}
d(E_x(P),E_x(Q)).
\]

Future extensions should add the rotation/associahedron graph and Lipschitz
variation of \(E_x\) across its edges.

## 7. CVCD finite matrix

Given explicit representations \(R_i\), a property \(P\), and metric \(d\),

\[
D^P_{ij}=d(P(R_i),P(R_j)).
\]

This is a finite diagnostic matrix, not automatically a tensor in the
coordinate-transformation sense. Any later use of the word *tensor* must
specify transformation laws.

## 8. Structural DNA

A Structural DNA record is a finite feature signature. Equality means equality
of the current canonicalized feature sets only.

The collision workflow is:

\[
DNA_\Omega(X)=DNA_\Omega(Y),\quad X\not\simeq Y
\Longrightarrow
\text{current signature is incomplete}.
\]

The response is to search for an additional discriminator, not to assert an
isomorphism.

## 9. Deferred R0.x definitions

The following are intentionally not faked in R0.1:

- global representation-space geometry;
- equivariant Tensor Spectrum beyond explicit representation-theory adapters;
- general logarithm obstruction classes;
- HGFM fractal dimension theorems;
- proof partition functions over infinite proof spaces;
- robust inverse theorems for zero tomography;
- universal dimension vectors;
- multigraded hypernumber algebra.

Each requires a specialized mathematical domain, baselines and explicit
hypotheses before promotion.
