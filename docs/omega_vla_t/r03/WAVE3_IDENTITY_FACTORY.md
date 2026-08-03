# Ω‑VLA‑T∞³ R0.3‑OMEGA — Wave 3 Identity Factory

## Status

Wave 3 is a deterministic research-software layer for declaring, mutating,
testing, falsifying and compiling finite matrix identities.

It does not claim:

- a new theorem;
- a solution to an open problem;
- completion of a formal proof;
- universal validity from randomized trials;
- scientific or experimental validation;
- infinite computation, storage or identity generation.

All generated objects retain:

```text
theorem_claimed = false
formal_proof_claimed = false
scientific_validation_claimed = false
```

## Operating loop

```text
schema
→ reversible address
→ typed instance
→ assumption mutation
→ finite fixture generation
→ residual test
→ counterexample / numerical support
→ M− record
→ Python or SMT target
→ OAK report
```

## Matrix-expression IR

`MatrixExpr` supports variables, identity, zero, sums, differences, products,
adjoint, transpose, inverse, powers, commutators, anticommutators, tensor
products and scalar multiplication. Expressions have deterministic JSON,
SHA-256 identity, finite NumPy semantics and conservative simplification.

## Assumption language

Finite numerical assumptions include:

- square;
- symmetric and skew-symmetric;
- Hermitian;
- unitary and orthogonal;
- projection;
- involution;
- invertible;
- normal;
- positive semidefinite;
- pairwise commuting.

Every check returns both a Boolean and a measured residual.

## Declarative catalog

The initial catalog contains 24 schemas, including:

- adjoint and transpose involution;
- adjoint/transpose distribution and product reversal;
- inverse reversal and double inverse;
- commutator antisymmetry and Leibniz rule;
- left/right distributivity and associativity;
- projection idempotence;
- unitary inverse-adjoint;
- involution square;
- commuting binomial square;
- tensor adjoint and mixed-product identities;
- normality and orthogonality conditional identities.

## Reversible candidate frontier

The mixed-radix frontier combines:

- 24 schemas;
- 16 dimensions;
- 2 scalar systems;
- 14 matrix families;
- 8 mutation policies;
- 6 trial profiles.

This yields **516,096 reversible logical candidates**. An address is a test
plan, not an executed identity and not evidence of truth. Traversal is
unique inside a requested window, deterministic, resumable by `start_offset`
and uses O(1) auxiliary memory.

## Mutation engine

Current policies:

- no mutation;
- drop one assumption;
- drop every assumption;
- strengthen with normality;
- strengthen with invertibility;
- strengthen with Hermiticity;
- swap adjoint and transpose;
- reverse selected left-side operands.

Weakening searches for missing hypotheses. Strengthening maps sufficient
condition neighborhoods. Neither operation proves necessity or minimality.

## Falsification and M−

Fixture families include dense, diagonal, symmetric, Hermitian, orthogonal,
unitary, projection, involution, singular, ill-conditioned, nilpotent, Jordan,
commuting and noncommuting matrices.

A failed candidate produces a content-addressed counterexample with matrices,
seed, trial, assumption audit, absolute and relative residuals, greedy
zero-entry minimization and claim flags forced false.

Example: removing the projection assumption from `A² = A` deterministically
produces a concrete finite counterexample.

## Property-test compiler

The Python compiler emits an executable finite property test using the same
schema, instance and falsifier APIs. Its status is `GENERATED_UNEXECUTED`
until an external runner executes it.

## SMT-LIB compiler

The SMT-LIB compiler emits a bounded real `QF_NRA` counterexample query for a
supported polynomial matrix subset.

Interpretation:

- `sat`: a finite counterexample exists under encoded assumptions;
- `unsat`: only the emitted bounded formula is unsatisfiable.

An `unsat` result is never promoted automatically to a universal theorem or a
formal proof. Unsupported complex, inverse and tensor expressions are marked
explicitly.

## Dependency graph

Schema parent relations form a closed directed acyclic graph with missing-parent
audits, cycle detection, topological ordering and ancestor queries.

## Campaign engine

A campaign materializes only its requested finite window and records:

- generated instances;
- numerically supported candidates;
- falsified candidates;
- incomplete trials;
- unique instance count;
- next resume offset;
- aggregate SHA-256;
- logical frontier size;
- `permanent_total_cap: null`.

Identical inputs produce identical reports.

## CLI

```bash
omega-vla-wave3 manifest
omega-vla-wave3 catalog --tag commutator
omega-vla-wave3 decode 42

omega-vla-wave3 test adjoint.product \
  --dimension 4 --scalar complex --family dense --trials 32

omega-vla-wave3 test projection.idempotence \
  --dimension 3 --mutation drop_all

omega-vla-wave3 smt commutator.identity_zero \
  --dimension 2 --scalar real

omega-vla-wave3 property-test adjoint.product \
  --dimension 4 --scalar complex

omega-vla-wave3 campaign \
  --count 1000 --seed 2026 --start-offset 0 --trials 4 \
  --output wave3-campaign.json

omega-vla-wave3 oak
```

## OAK checks

The dedicated audit verifies:

- catalog size;
- frontier size;
- 1,024 reversible address round trips;
- deterministic uniqueness;
- dependency closure and acyclicity;
- a known complex adjoint-product fixture;
- counterexample discovery after projection-assumption weakening;
- Python target claim boundaries;
- SMT target claim boundaries;
- global theorem/proof/scientific-validation flags.

Passing OAK means these declared software fixtures passed. It is not a
mathematical certification.

## Current limitations

- finite dense NumPy reference semantics only;
- randomized tests do not establish universality;
- greedy minimization is not globally minimal;
- assumption synthesis is heuristic;
- SMT encoding is real and polynomial-subset only;
- no external SMT or theorem prover is invoked;
- no interval or exact rational arithmetic yet;
- no distributed million-test execution yet.

These limitations feed Wave 4 Counterexample Superfactory and Wave 5 Proof
Genome rather than being hidden.
