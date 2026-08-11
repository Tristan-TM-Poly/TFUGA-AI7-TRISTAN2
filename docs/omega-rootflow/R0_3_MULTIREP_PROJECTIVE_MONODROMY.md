# Ω-ROOTFLOW-T∞ R0.3 — Multi-Representation, Projective Roots and Monodromy

R0.3 extends ROOTFLOW from local coefficient sensitivity to three structures that become essential when spectra are studied globally:

1. the **same polynomial in several coefficient coordinate systems**;
2. the **full nominal-degree root divisor on the projective line**, including infinity;
3. the **permutation of root branches produced by closed coefficient loops**.

The three layers are connected by one principle:

\[
\boxed{
\text{polynomial object}
\neq
\text{one coefficient vector}
\neq
\text{one affine root ordering}
}
\]

ROOTFLOW therefore separates the invariant polynomial/spectrum from the coordinates used to represent and follow it.

---

## 1. Multi-basis root calculus

R0.3 supports four coefficient systems:

- monomial / power basis;
- Chebyshev basis;
- Legendre basis;
- Bernstein basis on `[0,1]`.

For a native expansion

\[
P(z)=\sum_{k=0}^{n} c_k\phi_k(z),
\]

the exact simple-root differential is still

\[
\boxed{
\frac{\partial r_j}{\partial c_k}
=-\frac{\phi_k(r_j)}{P'(r_j)}
}.
\]

The polynomial object is unchanged, but the Jacobian coordinates change with the basis.

### Conversion invariant

For every supported representation `B`, the software checks the round trip

\[
P_{\rm power}
\rightarrow
c_B
\rightarrow
\widehat P_{\rm power}
\]

through the relative reconstruction residual

\[
\epsilon_B
=
\frac{\|P-\widehat P\|_2}{\|P\|_2}.
\]

A conditioning comparison is meaningful only when this reconstruction error is controlled.

### Bernstein conversion

For degree `n`,

\[
P(x)=\sum_{k=0}^{n}\beta_k B_{k,n}(x),
\qquad
B_{k,n}(x)=\binom nk x^k(1-x)^{n-k}.
\]

R0.3 implements exact finite combinatorial conversion between Bernstein and power coefficients. In the power-to-Bernstein direction,

\[
\boxed{
\beta_k
=
\sum_{j=0}^{k}
 a_j\frac{\binom{k}{j}}{\binom{n}{j}}
}.
\]

### Representation-dependent conditioning atlas

For each basis, ROOTFLOW computes native coefficient norm, native root-Jacobian row norms and the local relative sensitivity proxy

\[
\kappa_{j,B}
=
\frac{\|c_B\|_2\,\|J_{j,B}\|_2}{\max(|r_j|,\epsilon)}.
\]

This does **not** declare a universally best basis. It answers the narrower, testable question:

> for this polynomial, at this spectrum, under this coordinate norm, which supported representation has the smallest measured first-order root sensitivity?

That distinction is important because basis scaling, root location and coefficient domain all affect conditioning.

CLI:

```bash
python -m omega_rootflow_t basis-atlas \
  --coeffs '0.3,-1.2,0.4,1'
```

---

## 2. Projective root spectrum and roots at infinity

An affine polynomial of effective degree `m` may be embedded in a nominal degree `n>m` coefficient vector. Affine root solvers silently return only `m` finite roots. Projectively, the degree does not disappear.

Homogenize

\[
P(z)=\sum_{k=0}^{n}a_kz^k
\]

as

\[
\boxed{
F(u,v)=\sum_{k=0}^{n}a_k u^k v^{n-k}
}.
\]

Finite roots are points `[r:1]`. The point at infinity is `[1:0]`.

If

\[
a_n=a_{n-1}=\cdots=a_{m+1}=0,
\qquad a_m\neq0,
\]

then the nominal degree is `n`, the effective affine degree is `m`, and

\[
\boxed{
\text{multiplicity at infinity}=n-m.
}
\]

R0.3 represents those missing affine roots explicitly rather than discarding them.

Example:

\[
P(z)=z^2-1
\]

stored in a nominal degree-four vector

\[
[-1,0,1,0,0]
\]

has projective spectrum

\[
\{-1,+1,\infty,\infty\}.
\]

CLI:

```bash
python -m omega_rootflow_t projective \
  --coeffs=-1,0,1,0,0
```

### Chordal distance

Affine Euclidean distance diverges near infinity, so R0.3 exposes a homogeneous chordal distance. For normalized projective points `[u:v]` and `[u':v']`,

\[
\boxed{
d=|uv'-vu'|.
}
\]

This keeps finite-to-infinite comparisons bounded and creates the metric primitive needed for future projective branch matching during degree transitions.

### OAK boundary

R0.3 identifies exact roots at infinity when top coefficients vanish at the configured coefficient threshold. It does **not** yet provide a fully adaptive projective continuation algorithm for a coefficient tending continuously to zero. That is the next bridge between R0.2 degree activation and the projective spectrum.

---

## 3. Root monodromy from coefficient loops

Local continuation is not globally equivalent to assigning one permanent label to every root.

A closed loop in coefficient space can return to the same polynomial while permuting analytically continued root branches.

R0.3 tracks an ordered root vector using

\[
\boxed{
\text{analytic predictor}
\rightarrow
\text{Newton corrector}
\rightarrow
\text{direct-spectrum OAK set check}
\rightarrow
\text{carry branch ordering}
}.
\]

For a closed coefficient loop, the final ordered roots are matched back to the initial root set, yielding a permutation

\[
\sigma\in S_n.
\]

### Canonical square-root monodromy fixture

Consider

\[
P_t(z)=z^2-t,
\qquad t=e^{i\theta},
\qquad 0\le\theta\le2\pi.
\]

The loop encloses the discriminant point `t=0` without touching it.

Locally,

\[
r_\pm(t)=\pm\sqrt t.
\]

After one full turn in `t`, analytic continuation changes the sign of the square root. Therefore the two branches exchange:

\[
\boxed{
\sigma=(12).
}
\]

The software regression expects the zero-based permutation

```text
[1, 0]
```

while keeping corrected polynomial residuals near floating-point precision and `|P'(r)|` safely bounded away from zero along the loop.

CLI:

```bash
python -m omega_rootflow_t monodromy-demo \
  --samples 17 \
  --subdivisions 2
```

This fixture is particularly important because a solver that re-sorts roots independently at every point can miss the global branch exchange even though every local root set is numerically correct.

---

## 4. Connection to HGFM / Ω-STACK-T∞

R0.3 suggests a natural spectral hypergraph:

- coefficient-space points are hypernodes;
- local continuation steps are directed hyperedges;
- each root branch is a fiber over the coefficient node;
- discriminant components are singular strata;
- closed loops carry monodromy permutations;
- basis changes are representation morphisms;
- projective infinity is an explicit compactification node rather than a numerical overflow state.

The resulting object is suitable for a future **HGFM spectral branch graph** where loops, collisions, root births from infinity and basis changes can coexist in one auditable representation.

---

## 5. Validation matrix

R0.3 adds tests for:

1. power ↔ monomial/Chebyshev/Legendre/Bernstein round trips;
2. native Chebyshev root Jacobian against a finite coefficient perturbation;
3. reconstruction invariants in the basis conditioning atlas;
4. nominal-degree preservation with explicit infinity multiplicity;
5. finite projective distance to infinity;
6. non-trivial transposition monodromy for `z^2-exp(i theta)`;
7. JSON CLI surfaces for basis atlas, projective roots and monodromy.

All R0.1 and R0.2 tests remain active.

---

## 6. OAK claim boundary

R0.3 combines established polynomial identities and numerical implementations. It does not claim new theorems about monodromy, discriminants, projective algebraic geometry or optimal polynomial bases.

Exact/established structure used by the implementation includes:

- basis conversion identities;
- implicit simple-root differentiation;
- homogenization of a polynomial;
- roots at `[1:0]` when nominal leading coefficients vanish;
- branch permutation under analytic continuation around discriminant loci.

Numerical/software claims include:

- conversion residuals;
- Jacobian finite-perturbation agreement;
- branch tracking accuracy;
- Newton corrected residuals;
- measured conditioning proxies;
- recovered permutation for deterministic fixtures.

Every R0.3 report preserves `theorem_claimed=false` and `scientific_validation_claimed=false` where claim metadata is emitted.

---

## 7. Next executable waves

The most direct R0.4 extensions are:

1. projective predictor-corrector continuation through leading-coefficient degree transitions;
2. Puiseux local coordinates near multiplicity-`m` collisions;
3. monodromy-group generation from multiple loops and permutation closure;
4. discriminant-locus sampling and HGFM branch graph construction;
5. basis-domain scaling/translation atlas instead of fixed canonical domains;
6. polynomial-matrix and generalized-eigenvalue ROOTFLOW;
7. nonlinear Monte Carlo uncertainty vs `J Sigma J^H` calibration;
8. CVCD/FFWT compression of branch trajectories and large spectra.
