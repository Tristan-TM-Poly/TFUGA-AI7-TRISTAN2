# Ω-DISCOVERY-GEOMETRY-ALGEBRA-T R0.3

Status: executable research prototype / OAK-bounded deterministic fixtures.

R0.3 extends MetaScienceBench R0.1 and Discovery Dynamics R0.2 with a small algebra and geometry of discovery. The goal is not to multiply names. The goal is to expose reusable operators for equivalence, adversarial alternatives, evidence dependence, second-order utility sensitivity, contradiction minimization, certified transforms, and finite scientific-program optimization.

## Mother pipeline

```text
theory population
  -> empirical quotient
  -> adversarial twin
  -> evidence-independence audit
  -> local Hessian of declared utility
  -> minimal contradiction core
  -> proof-carrying transforms
  -> finite scientific superoptimization
```

Every arrow has an explicit OAK boundary.

## 1. Empirical Theory Quotient

`empirical_theory_quotient()` groups theories whose predictions are indistinguishable on a declared finite probe set within a declared tolerance.

For the canonical fixture:

```text
T_linear:    y = x
T_quadratic: y = x^2
```

on probes `{0,1}` the theories are observationally aliased and form one empirical class. Adding probe `2` splits them into two classes.

This is the exact lesson the quotient is intended to preserve:

```text
same on current probes != mathematically equivalent
```

R0.3 does not infer symbolic equivalence, coordinate equivalence, observational equivalence over a continuum, or historical novelty.

## 2. Anchor-Preserving Adversarial Twin

`compile_adversarial_twin()` searches one finite perturbation family

\[
T_\alpha(x)=T(x)+\alpha\prod_j(x-a_j),
\]

where the `a_j` are declared anchors. Every family member matches the base theory exactly at those anchors, while possibly diverging elsewhere.

The fixture anchors the linear theory at `x=0,1` and searches finite `alpha` values. The strongest challenge occurs at `x=3` with divergence `6`.

This operationalizes an important discipline:

```text
a theory should confront plausible alternatives that fit what is already known
```

Boundary: this is only the strongest rival in one declared finite perturbation family.

## 3. Evidence Independence Tensor Surrogate

`evidence_independence()` accepts a symmetric pairwise dependence matrix with unit diagonal and entries in `[0,1]`.

It computes the bounded surrogate

\[
N_{eff}=\frac{N^2}{\sum_{ij} C_{ij}},
\]

clipped to `[1,N]` for a valid non-empty matrix.

For three evidence items where `E1` and `E2` have dependence `0.9` and `E3` is independent,

\[
N_{eff}=1.875 < 3.
\]

The purpose is to prevent duplicated or genealogically coupled evidence from being naively counted as independent support.

Boundary: this is a declared redundancy surrogate, not a universal effective-sample-size theorem.

## 4. Epistemic Hessian

R0.2 introduced a local first derivative of a declared disagreement surrogate. R0.3 generalizes to a central finite-difference Hessian of any explicitly supplied scalar utility

\[
H_{ij}=\frac{\partial^2 U}{\partial a_i\partial a_j}.
\]

The cross terms expose local interaction between actions or design coordinates. A non-zero off-diagonal term can signal complementarity or interference in the chosen surrogate.

The fixture uses

\[
U(a,b)=-(a-2)^2-2(b-3)^2+\frac12ab,
\]

whose exact Hessian is

\[
\begin{pmatrix}-2 & 0.5\\0.5 & -4\end{pmatrix}.
\]

CI checks the numerical Hessian against that analytic result.

Boundary: this is curvature of a declared utility surrogate, not curvature of truth or scientific knowledge itself.

## 5. Claim UNSAT Core

`minimal_unsat_core()` works over an explicit finite world model. Each claim declares the worlds it allows. If the total claim set is inconsistent, R0.3 searches subsets in increasing cardinality and returns a cardinality-minimal inconsistent core.

Fixture:

```text
C1 allows {A,B}
C2 allows {B,C}
C3 allows {A,C}
```

Every pair is satisfiable, but the triple intersection is empty. Therefore the minimal core is exactly `{C1,C2,C3}`.

This is useful for large knowledge graphs because it changes

```text
"the corpus is contradictory"
```

into

```text
"these exact claims are jointly contradictory in this declared finite world model"
```

Boundary: no general SAT/SMT, theorem proving, or unrestricted first-order inconsistency result is claimed.

## 6. Proof-Carrying Transform Certificate

`TransformCertificate` makes a scientific transform carry:

- source and target identities;
- declared invariants before and after;
- round-trip error;
- maximum allowed error;
- domain;
- provenance.

`validate_transform_certificate()` fails closed on missing provenance/domain, error-bound violation, negative bounds, or lost required invariants.

The intended reusable pattern is

\[
X\xrightarrow{\Phi,I,\epsilon,D,Prov}Y.
\]

A transform is not accepted merely because it produces an output.

## 7. Scientific Superoptimizer

`scientific_superoptimize()` selects the least-cost candidate only after hard gates:

```text
OAK PASS
+ verified gain >= threshold
+ required invariants retained
```

The fixture includes:

- a valid baseline costing `10`;
- a valid compressed program costing `4`;
- a superficially cheap invalid program costing `1`.

The invalid program is rejected before cost ranking. The compressed valid program wins and reports savings of `6` relative to the most expensive eligible candidate.

Boundary: this is finite candidate selection, not global optimization over every possible scientific workflow.

## 8. Composed R0.3 fixture

`run_discovery_geometry_algebra_demo()` composes all seven primitives:

```text
coarse probes -> one empirical theory class
refined probes -> two classes
anchor twin -> exact anchor retention + off-anchor divergence
evidence matrix -> N_eff < N
Hessian -> analytic finite-difference cross-check
claim set -> minimal contradiction core
transform -> certificate PASS
program set -> compressed valid program selected
```

Replay:

```bash
python -m omega_meta_science_t.geometry_cli
python -m omega_meta_science_t.geometry_cli --compact
```

Tests:

```bash
python -m pytest -q \
  tests/test_omega_meta_science_t.py \
  tests/test_omega_meta_science_discovery.py \
  tests/test_omega_meta_science_geometry.py
```

## 9. What R0.3 demonstrates

It demonstrates executable, composable interfaces for:

- finite empirical theory quotienting;
- constrained adversarial-rival generation;
- declared evidence-dependence discounting;
- second-order sensitivity of a supplied utility;
- finite contradiction-core minimization;
- transform certification;
- constraint-first finite program optimization.

## 10. What R0.3 does not demonstrate

R0.3 does not establish:

- mathematical equivalence classes of arbitrary theories;
- globally strongest adversarial theories;
- universal statistical independence estimation;
- a physical geometry of knowledge;
- general theorem proving;
- globally optimal research programs;
- historical novelty of the names or individual concepts;
- general scientific superiority.

## 11. R0.4 promotion path

The strongest next increment is not another naming expansion. It is to replace toy declarations with measurable external structure:

1. symbolic/semantic theory canonicalization with round-trip tests;
2. adversarial twins generated from model families with held-out data;
3. evidence-dependence inferred from provenance graphs and shared datasets;
4. experiment-portfolio Hessians on recognized active-learning benchmarks;
5. SAT/SMT-backed contradiction cores for typed claims;
6. proof-carrying transforms over real symbolic/numeric representation changes;
7. superoptimization ablations under equal compute and experiment budgets;
8. lineage/bisect attribution of which mutation created or destroyed verified gain.

Operating law:

```text
quotient carefully -> generate a rival -> discount dependent evidence -> inspect interaction -> minimize contradiction -> certify transforms -> optimize only after OAK
```
