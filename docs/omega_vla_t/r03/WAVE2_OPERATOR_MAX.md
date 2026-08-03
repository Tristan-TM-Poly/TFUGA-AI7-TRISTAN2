# Ω-VLA-T∞³ R0.3-OMEGA — Wave 2 Operator MAX

## Purpose

Wave 2 expands the typed VLA-IR foundation from PR #316 into an executable,
addressable and evidence-aware Operator Universe.

The objective is not to duplicate hundreds of thousands of source lines. The
objective is to define compact kernels capable of producing and auditing large
families of operator assets while preserving assumptions, units, residuals,
provenance and epistemic status.

```text
VLA-IR
-> typed operator family
-> representation
-> algorithm
-> evidence
-> residual
-> benchmark
-> genome
-> OAK
```

## Scope implemented

Wave 2 adds:

- a deterministic catalog of more than 300 operator families;
- dependency-light CSR sparse matrices;
- finite matrix-free operators;
- bounded matrix functions;
- evidence-aware numerical property inference;
- commutant and simultaneous-centralizer solvers;
- bounded equality-saturation-style rewriting;
- content-addressed operator genomes;
- an SQLite genome registry;
- deterministic benchmark atlases;
- a reversible logical campaign frontier;
- dedicated CLIs, schemas, tests, demonstration and CI.

## OAK status

Wave 2 implements research-software fixtures. It does not claim:

- a new theorem;
- a solution to an open problem;
- completed formal proofs;
- scientific or experimental validation;
- universal semantics for unbounded operators;
- infinite memory, storage or compute;
- that a catalog entry is implemented;
- that a logical campaign address is an executed test;
- that a numerical residual establishes mathematical truth.

Generated objects preserve:

```text
theorem_claimed = false
formal_proof_claimed = false
scientific_validation_claimed = false
```

## 1. Operator family catalog

`families.py` declares stable metadata for operator families across:

1. foundations;
2. structured matrices;
3. spectral matrix functions;
4. differential operators;
5. graph, hypergraph and complex operators;
6. tensor and multilinear operators;
7. dynamics and control;
8. physical equation operators;
9. transforms;
10. optimization and probability.

Each family records:

- a stable identifier;
- realm and order;
- semantic class;
- parameters;
- assumptions;
- candidate properties;
- applications;
- maturity.

A family in state `declared` is an addressable target, not an implementation.
Only selected families in state `reference_fixture` can currently be
materialized numerically.

### Query the catalog

```bash
omega-vla-wave2 catalog --realm physics --limit 20
omega-vla-wave2 catalog --text Hodge
omega-vla-wave2 catalog --application spectroscopy
```

### Materialize a reference fixture

```bash
omega-vla-wave2 materialize \
  discrete_geometry.graphs_complexes.combinatorial_laplacian \
  --dimension 32 \
  --dense
```

Current reference fixtures include:

- identity;
- zero;
- diagonal;
- circulant;
- Hilbert;
- permutation;
- first derivative;
- second derivative;
- path-graph Laplacian;
- mass matrix;
- stiffness matrix.

## 2. CSR sparse kernel

`CSRMatrix` implements canonical compressed sparse row storage with:

- validation of `data`, `indices`, `indptr` and shape;
- canonical sorted row indices;
- duplicate accumulation through COO ingestion;
- dense conversion under an element budget;
- sparse matvec;
- transpose and adjoint;
- addition;
- scaling;
- bounded sparse multiplication;
- bounded Kronecker products;
- identity, diagonal and one-dimensional Laplacian constructors;
- deterministic SHA-256 identity.

This is a reference kernel. Mature SciPy, SuiteSparse, Eigen, MKL, CUDA and
Rust sparse libraries remain future comparison backends.

## 3. Matrix-free operators

`MatrixFreeOperator` stores an action instead of a dense matrix.

It supports:

- declared domain and codomain dimensions;
- optional named spaces;
- scalar and unit metadata;
- `matvec` and optional `rmatvec`;
- composition;
- addition;
- scaling;
- adjoint construction;
- bounded materialization;
- randomized linearity audit;
- randomized adjoint audit;
- norm upper estimates.

Example:

```python
import numpy as np
from omega_vla_t.r03.wave2 import MatrixFreeOperator

matrix = np.array([[2.0, 1.0], [0.0, 3.0]])
operator = MatrixFreeOperator.from_dense(matrix, name="A")
report = operator.audit(trials=32, seed=2026)
```

An audit passing at a declared tolerance means the finite software fixture
passed those tests. It does not prove linearity for an arbitrary external
callable.

## 4. Matrix functions

`matrix_functions.py` implements bounded reference methods:

| Function | Method |
|---|---|
| exponential | Padé [13/13] with scaling and squaring |
| logarithm | inverse scaling plus atanh series |
| square root | Denman–Beavers iteration |
| sign | Newton iteration |

Each result contains:

- method;
- result matrix;
- residual identity;
- iteration count;
- scaling count;
- condition estimate;
- finite flag;
- pass/fail status;
- warnings.

Examples:

```bash
omega-vla-wave2 matrix-function exp '[[0,-0.2],[0.2,0]]'
omega-vla-wave2 matrix-function log '[[1,0],[0,2]]'
omega-vla-wave2 matrix-function sqrt '[[1,0],[0,4]]'
omega-vla-wave2 matrix-function sign '[[-2,0],[0,3]]'
```

### Rejection conditions

The logarithm rejects:

- singular matrices;
- numerical eigenvalues on the closed negative real axis.

The sign iteration rejects eigenvalues near the imaginary axis.

Linear solves reject excessive condition estimates.

These are conservative software boundaries, not complete analytic domain
characterizations.

## 5. Evidence-aware properties

`infer_properties` produces `PropertyEvidence` records rather than naked
booleans.

Current evidence includes:

- zero;
- identity;
- self-adjoint;
- skew-adjoint;
- normal;
- unitary;
- projection;
- involution;
- invertible;
- positive semidefinite;
- positive definite;
- numerical rank;
- trace;
- spectral radius.

Every record preserves:

- `supported: true`, `false` or `null`;
- evidence level;
- residual;
- threshold;
- method;
- assumptions;
- witnesses;
- false theorem and formal-proof flags.

```bash
omega-vla-wave2 properties '[[1,0],[0,2]]'
```

## 6. Commutants and centralizers

For a finite square matrix `A`, Wave 2 forms the linear constraint:

```text
vec(A X - X A) = (I kron A - A^T kron I) vec(X)
```

The null space is estimated by dense SVD.

The report includes:

- ambient dimension;
- estimated nullity;
- singular values;
- basis matrices;
- maximum commutator residual;
- residual for identity membership in the span.

```bash
omega-vla-wave2 commutant '[[1,0],[0,2]]'
```

Multiple matrices request a simultaneous commutant:

```bash
omega-vla-wave2 commutant \
  '[[1,0],[0,2]]' \
  '[[0,1],[1,0]]'
```

The dense SVD implementation is intentionally bounded by `max_dimension`.

## 7. Bounded rewrite saturation

`egraph.py` explores equivalent `OperatorExpr` objects under explicit budgets:

- rounds;
- expressions;
- total nodes;
- nodes per expression.

Current local identities include:

- existing R0.3 simplification rules;
- commutator expansion and antisymmetry;
- anticommutator expansion and symmetry;
- adjoint rules;
- inverse of composition;
- low-order powers;
- distributivity of composition;
- distributivity of tensor products.

The result reports all accepted rewrite events and extracts the expression with
lowest `(node_count, depth, digest)` cost.

This is a compact deterministic saturation engine, not yet a complete e-graph
with union-find congruence closure.

## 8. Operator genomes

An `OperatorGenome` binds:

- family identity;
- concrete mathematical type;
- representation;
- parameters;
- assumptions;
- invariants;
- algorithms;
- backends;
- property evidence;
- residuals;
- provenance;
- epistemic status.

The SQLite registry provides:

- exact content-addressed deduplication;
- unique `genome_id` enforcement;
- indexes by family and status;
- deterministic JSONL export;
- summary reports.

```bash
omega-vla-wave2 genome-demo --database generated/vla-genomes.sqlite3
```

## 9. Benchmark multiverse

The deterministic reference atlas compares:

- CSR action against dense action;
- sparse adjoint identities;
- matrix-free linearity and adjoint tests;
- evidence-aware properties;
- commutant dimensions for bounded cases;
- matrix-function residuals.

Default reports omit runtime measurements. Optional runtime values are marked
as environmental and removed from the deterministic digest.

```bash
omega-vla-wave2 benchmark --dimensions 4,8,16
```

The logical benchmark frontier includes axes for:

- family;
- dimension;
- sparsity;
- condition;
- rank;
- noise;
- precision;
- backend;
- hardware class;
- question.

Logical size does not mean the cases have been executed.

## 10. Campaign frontier

`OperatorCampaignCodec` adds reversible axes for:

- family;
- dimension;
- representation;
- scalar system;
- property question;
- backend;
- condition regime;
- sparsity regime;
- tolerance;
- application;
- method.

The resulting frontier exceeds one trillion addresses without materializing a
large array or permutation.

```bash
omega-vla-wave2-campaign manifest
omega-vla-wave2-campaign decode 123456789
omega-vla-wave2-campaign plan --count 100000 --seed 2026
omega-vla-wave2-campaign audit-roundtrip --count 10000
```

Continuation is represented by `start_offset`:

```bash
omega-vla-wave2-campaign plan \
  --count 100000 \
  --seed 2026 \
  --start-offset 500000
```

A plan is not an execution report.

## 11. OAKBench

```bash
omega-vla-wave2 oak
```

The Wave 2 audit checks:

1. family count and deterministic catalog digest;
2. CSR/dense equivalence;
3. sparse identity multiplication;
4. matrix-free linearity and adjoint residuals;
5. exponential, logarithm, square-root and sign residuals;
6. evidence-aware positive-definite and non-unitary fixtures;
7. commutant dimensions and identity span;
8. bounded rewrite extraction;
9. genome-registry deduplication;
10. deterministic benchmark atlas;
11. logical frontier size with no permanent cap.

Success status:

```text
OAK_PASS_SOFTWARE_RESEARCH_FIXTURES_R0_3_WAVE_2
```

This status means only that the declared software fixtures passed.

## 12. Tests

Focused suites:

```text
tests/test_omega_vla_r03_wave2_sparse_functions.py
tests/test_omega_vla_r03_wave2_catalog_commutant.py
tests/test_omega_vla_r03_wave2_cli_oak.py
tests/test_omega_vla_r03_wave2_campaigns.py
```

Coverage includes:

- canonical CSR validation;
- matrix-free composition;
- matrix-function identities;
- principal-logarithm rejection;
- positive-definite versus semidefinite evidence;
- catalog stability;
- reference materializers;
- commutant dimensions;
- bounded saturation;
- persistent genome deduplication;
- CLI output;
- OAK claims;
- campaign round trips and non-overlapping resume offsets.

## 13. Machine-readable contracts

```text
schemas/omega_vla_operator_genome_v2.schema.json
schemas/omega_vla_wave2_campaign_plan_v1.schema.json
```

The schemas force generated theorem, formal-proof and scientific-validation
claims to remain false.

## 14. Limitations

Wave 2 does not yet implement:

- production sparse factorizations;
- distributed sparse matrices;
- GPU kernels;
- stable Schur decomposition backends;
- rational Krylov matrix functions;
- full e-graph congruence closure;
- symbolic domain analysis for unbounded operators;
- automatic formal proofs;
- physical-equation discretization;
- global distributed genome deduplication.

These belong to later waves or dedicated PRs.

## 15. Stack order

```text
PR #299  R0.1 numerical kernel
PR #302  R0.2-MAX research frontier
PR #316  R0.3 Wave 1 VLA-IR and type system
Wave 2   Operator MAX, based on PR #316 head
```

Merge or retarget in stack order.

## 16. Canonical rule

```text
catalog entry != implementation
implementation != tested fixture
tested fixture != theorem
logical address != executed experiment
small residual != universal validity
large volume != scientific value
```

The useful growth loop is:

```text
family
-> typed genome
-> implementation
-> evidence
-> counterexample search
-> benchmark
-> formal target
-> application
-> canon or M-minus
```
