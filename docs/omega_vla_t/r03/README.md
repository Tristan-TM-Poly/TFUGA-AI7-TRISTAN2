# Ω-VLA-T∞³ R0.3-OMEGA — Wave 1

## VLA-IR, mathematical typing and Operator Universe

R0.3-OMEGA begins the transition from a numerical library and research-frontier
compiler toward a mathematical operating system.  This wave implements the
foundational contracts needed before large-scale generation:

1. mathematical types;
2. VLA-IR typed graphs;
3. a typed operator-expression grammar;
4. bounded finite-matrix semantics;
5. deterministic compilation backends;
6. identity and counterexample fixtures;
7. OAK gates 0 through 11.

The implementation is intentionally narrower than the complete R0.3 vision.
It does not yet formalize arbitrary Banach spaces, unbounded operators,
manifolds, distributions, non-associative scalar algebras or physical PDEs.
Those objects can be represented as IR nodes, but they require dedicated
semantics before numerical or formal compilation.

---

## 1. Epistemic boundary

R0.3-Wave-1 provides software contracts and finite numerical fixtures.  It does
not claim:

- a new theorem;
- a solution to an open mathematical problem;
- completed Lean, Coq or Isabelle proofs;
- scientific or experimental validation;
- universal correctness of generated source;
- infinite compute, storage or testing capacity;
- validity of HGFM, CVCD, FFWT or hypercomplex extensions.

Generated reports preserve:

```text
theorem_claimed = false
formal_proof_claimed = false
scientific_validation_claimed = false
```

Numerical support can expose implementation regressions or counterexamples.  It
cannot prove a universal identity.

---

## 2. Mathematical type system

`omega_vla_t.r03.types` represents a conservative finite contract:

```text
MathType(
    structure,
    scalar_system,
    shape,
    units,
    variance,
    regularity,
    support,
    uncertainty,
    domain_id,
    codomain_id,
    tags,
)
```

### Scalar systems

The first wave recognizes identifiers for:

- booleans;
- naturals;
- integers;
- rationals;
- reals;
- complexes;
- quaternions;
- octonions;
- sedenions;
- finite fields;
- real intervals.

Only the conventional embedding chain

```text
B -> N -> Z -> Q -> R -> C
```

is implicit.  For example, complex/quaternion coercion is rejected rather than
invented.  Noncommutative and nonassociative scalar semantics require explicit
future backends.

### Shapes

`Shape` supports finite and symbolic dimensions:

```python
Shape.of(3, 4)
Shape.of("n", "m")
```

Finite evaluators require concrete dimensions.  Symbolic shapes remain useful
for IR construction and source generation.

### Units

`UnitDimension` stores exact rational powers of seven SI base dimensions:

```python
L = UnitDimension.base("L")
T = UnitDimension.base("T")
velocity = L / T
acceleration = L / T.power(2)
```

It checks dimensional compatibility, not scale conversion.  Metres and
centimetres share a dimension and need a separate conversion layer.

### Domain and codomain identities

Two `3 x 3` matrices are not automatically composable when one acts on space
`V` and another maps into unrelated space `W`.  Named spaces are checked in
addition to dimensions.

---

## 3. VLA-IR

`VLAProgram` is a typed directed multigraph.

### Node classes

- spaces;
- scalars;
- vectors and covectors;
- matrices and tensors;
- operators;
- fields and forms;
- graphs and chain complexes;
- equations and assumptions;
- propositions and proof targets;
- tests and experiments;
- residuals and counterexamples;
- generated artifacts.

### Relation classes

- membership;
- domain and codomain;
- action and output;
- composition;
- dual and adjoint;
- invariance;
- approximation and generalization;
- discretization;
- proof and falsification;
- dependency;
- assumptions and residuals;
- commutation and noncommutation.

### Provenance

Every important node can retain:

```text
source
locator
method
confidence
license
notes
```

Missing provenance generates an OAK warning rather than silently disappearing.

### Canonical identity

Nodes and edges are sorted before JSON serialization.  A SHA-256 digest is
computed from the canonical payload, allowing content-addressed manifests,
reproducibility checks and deduplication.

### Dependency graph

An edge

```text
A DEPENDS_ON B
```

means `B` must precede `A`.  Cycles are detected before compilation.

---

## 4. Operator Universe

`OperatorExpr` separates symbolic syntax from finite numerical semantics.

### Implemented constructors

- symbol;
- identity;
- zero;
- matrix literal;
- sum and difference;
- composition;
- scalar multiplication;
- adjoint, transpose and conjugate;
- inverse and pseudoinverse;
- integer powers;
- exponential and logarithm reference nodes;
- commutator and anticommutator;
- tensor product;
- direct sum and Kronecker sum;
- low-rank update;
- typed placeholders for projection, derivative, multiplication, translation,
  restriction and extension.

Typed placeholders are not numerically executable until a backend provides
semantics.

### Composition order

```python
A @ B
```

represents `A composed with B` and evaluates as matrix product `A @ B`.

### Simplification rules

Wave 1 includes conservative rules such as:

```text
A I -> A
I A -> A
A + 0 -> A
A - A -> 0
(A*)* -> A
(AB)* -> B* A*
[A,A] -> 0
[A,I] -> 0
```

Simplification must converge within a finite pass budget.  It does not perform
unbounded theorem search.

---

## 5. Finite numerical semantics

`evaluate_operator` evaluates finite concrete matrices using NumPy.

### Resource envelopes

```python
EvaluationLimits(
    max_nodes=100_000,
    max_matrix_elements=25_000_000,
    max_power=1024,
)
```

These are per-execution safety envelopes, not permanent system ceilings.
Larger campaigns should benchmark and explicitly raise measured limits.

### Matrix functions

The initial exponential/logarithm reference implementation uses an
eigendecomposition and rejects ill-conditioned eigenvector matrices.  It is a
fixture, not a replacement for stable Schur/Padé algorithms in SciPy or
specialized libraries.

---

## 6. Compilation backends

### NumPy

Generates an `evaluate(environment)` function and explicit claim-boundary
constants.

### LaTeX

Generates a deterministic mathematical expression.

### Rust/nalgebra

Generates a bounded subset for matrix literals, symbols, sums, compositions,
adjoints and commutators.  Unsupported trees are marked incomplete.

### Lean 4

Generates an explicit-incomplete target carrying the serialized expression and
digest.  The file proves only `True`; it never pretends the operator identity
has been formalized or proved.

### GraphML

Compiles VLA-IR nodes and relations for graph inspection.

### JSON

Preserves the complete operator tree in a machine-readable format.

---

## 7. Identity and Counterexample Factory

Implemented schemas include:

- adjoint of a composition;
- commutator antisymmetry;
- commutator with identity;
- tensor-product adjoint;
- conditional projection idempotence.

`run_identity_trials` generates deterministic finite matrices and measures
relative residuals.  A failed trial produces a concrete environment.

`minimize_matrix_counterexample` greedily removes entries while preserving the
violation, creating a smaller M-minus asset.  This minimizer is heuristic and
does not guarantee a globally minimal counterexample.

---

## 8. OAK Gates

Every IR program or operator expression can be audited through:

```text
Gate 0  syntax
Gate 1  typing
Gate 2  units
Gate 3  domain/codomain
Gate 4  assumptions, provenance or simplification
Gate 5  dependencies or backend compilation
Gate 6  numerical evaluation / counterexample routing
Gate 7  counterexample or baseline routing
Gate 8  stability
Gate 9  formal proof
Gate 10 reproduction
Gate 11 canonical promotion
```

Only applicable gates are required to pass.  Non-applicable research gates are
reported as informational, not silently marked successful.

`OAK_PASS` means the declared software fixture passed the implemented gates.
It does not mean mathematical or scientific validation.

---

## 9. CLI

### Manifest

```bash
omega-vla-r03 manifest
```

### VLA-IR fixture

```bash
omega-vla-r03 ir-demo --format json --output /tmp/program.json
omega-vla-r03 ir-demo --format graphml --output /tmp/program.graphml
omega-vla-r03 audit-ir /tmp/program.json
```

### Operator fixture

```bash
omega-vla-r03 operator-demo --output /tmp/operator-report.json
```

### Compile an operator JSON tree

```bash
omega-vla-r03 compile expression.json --backend numpy --output generated.py
omega-vla-r03 compile expression.json --backend latex --output expression.tex
omega-vla-r03 compile expression.json --backend rust-nalgebra --output operator.rs
omega-vla-r03 compile expression.json --backend lean4 --output target.lean
```

### Identity suite

```bash
omega-vla-r03 identity-suite --trials 64 --seed 2026
```

---

## 10. Python example

```python
import numpy as np
from omega_vla_t.r03 import (
    MathType,
    OperatorExpr,
    ScalarSystem,
    audit_operator_expression,
    evaluate_operator,
)

operator_type = MathType.linear_operator(
    2,
    2,
    scalar_system=ScalarSystem.COMPLEX,
    domain_id="V",
    codomain_id="V",
)
A = OperatorExpr.symbol("A", operator_type)
B = OperatorExpr.symbol("B", operator_type)
expression = A.commutator(B)

environment = {
    "A": np.array([[0, 1], [-1, 0]], dtype=complex),
    "B": np.diag([1, 2]).astype(complex),
}

print(evaluate_operator(expression, environment).to_dict())
print(audit_operator_expression(expression, environment).to_dict())
```

---

## 11. Architecture of this wave

```text
omega_vla_t/r03/
├── __init__.py
├── cli.py
├── compilers.py
├── evaluator.py
├── fixtures.py
├── identities.py
├── ir.py
├── oak.py
├── operators.py
└── types.py
```

Schemas:

```text
schemas/
├── omega_vla_ir_v1.schema.json
└── omega_vla_operator_expr_v1.schema.json
```

Tests:

```text
tests/
├── test_omega_vla_r03_ir_types.py
└── test_omega_vla_r03_operators.py
```

---

## 12. Next waves

### Wave 2 — Operator Universe expansion

- stable matrix functions using Schur/Padé/Krylov backends;
- sparse and matrix-free semantics;
- derivative and multiplication operators;
- rewrite-rule registry with proof obligations;
- expression e-graphs and cost-based extraction;
- operator-property inference with evidence states.

### Wave 3 — Identity Factory

- generated property-based tests;
- SMT-compatible finite schemas;
- symbolic assumptions;
- theorem mutations;
- counterexample families and M-minus registry.

### Wave 4 — Geometry and tensors

- index-aware contractions;
- metric raising/lowering;
- exterior forms;
- Lie and Clifford operators;
- manifold charts and connections.

### Wave 5 — Physical compilers

- mechanics;
- diffusion and waves;
- Maxwell;
- fluid projection;
- elasticity;
- Raman and crystal tensors.

---

## 13. Anti-volume rule

This wave is not complete because it has many lines.  It is useful only insofar
as it creates reusable contracts:

```text
type
-> IR
-> operator
-> backend
-> test
-> falsifier
-> OAK report
```

The future million-scale campaigns should generate assets through these
contracts rather than copy-pasting source files.
