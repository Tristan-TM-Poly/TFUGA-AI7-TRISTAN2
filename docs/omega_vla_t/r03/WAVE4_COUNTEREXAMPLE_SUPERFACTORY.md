# Ω-VLA-T∞³ R0.3 — Wave 4 Counterexample Superfactory

## Purpose

Wave 4 makes falsification a first-class production system. It takes a finite
matrix conjecture, searches explicitly bounded adversarial families, preserves
assumption audits and residuals, minimizes discovered witnesses, proposes
candidate hypothesis repairs and stores accepted M-minus assets in a
content-addressed registry.

```text
conjecture
→ finite search plan
→ adversarial family
→ assumption audit
→ residual evaluation
→ counterexample
→ minimization
→ repair proposal
→ SQLite M-minus registry
→ regression asset
```

## OAK boundary

Wave 4 produces finite research-software evidence. It does not claim:

- that failure to find a witness proves a conjecture;
- that one witness characterizes every failure mode;
- that a proposed repair is sufficient or necessary;
- that randomized or bounded testing is a formal proof;
- that a logical frontier address is an executed search;
- unlimited compute, memory, storage or CI.

All generated objects retain:

```text
theorem_claimed = false
formal_proof_claimed = false
scientific_validation_claimed = false
```

## Search families

Wave 4 includes deterministic generators for dense, diagonal, symmetric,
skew-symmetric, Hermitian, unitary, orthogonal, projection, involution,
singular, rank-one, ill-conditioned, nilpotent, Jordan, Toeplitz, circulant,
permutation and sparse-event matrices.

Every generated environment retains family, scalar system, seed, dimension and
variable names.

## Counterexample minimization

The minimizer is predicate preserving. A transformation is accepted only when
the assumptions remain satisfied and the violation remains above tolerance.

Current stages:

1. principal-submatrix reduction;
2. zero-entry deletion;
3. quantization toward `0`, `±1`, `±i` and `±1/2`.

The trace records accepted and rejected transformations, dimensions and nonzero
counts before and after minimization.

## Repair proposals

Finite residuals are measured for candidate properties including symmetry,
Hermiticity, normality, projection, involution, unitarity, invertibility and
pairwise commutation. A repair proposal is an evidence-labelled hypothesis
candidate. It must be retested independently and is never promoted to theorem
status automatically.

## Addressable frontier

The mixed-radix frontier combines:

- 64 conjecture slots;
- 32 dimensions;
- 2 scalar systems;
- 18 matrix families;
- 8 search strategies;
- 6 minimizers;
- 6 trial profiles;
- 128 seeds.

This yields **2,717,908,992 logical plans**. They are addressable plans, not
executed searches or mathematical results. Traversal is reversible, resumes
from an exact offset and requires constant auxiliary memory.

## Registry

`CounterexampleRegistry` uses SQLite/WAL and stores stable identifiers,
conjecture identifiers, canonical digests, states, residuals and JSON payloads.
Duplicate content is rejected through a unique digest constraint. Deterministic
JSONL export supports downstream M-minus ingestion.

## Built-in OAK fixtures

The audit checks:

- frontier encode/decode round trips;
- frontier scale above one billion plans;
- deterministic campaign manifests;
- falsification of unconditional matrix commutativity;
- absence of a witness for the finite transpose-product fixture;
- projection idempotence on generated projection fixtures;
- SQLite content deduplication.

A passing audit certifies these software fixtures only.

## CLI

```bash
omega-vla-wave4 manifest
omega-vla-wave4 decode 123456
omega-vla-wave4 plan --start-offset 4096 --count 1024
omega-vla-wave4 search unconditional_commutativity \
  --dimension 2 --family dense --trials 16
omega-vla-wave4 oak
```

## Validation

```bash
python -m compileall -q \
  omega_vla_t/r03/wave4 \
  tests/test_omega_vla_r03_wave4.py \
  examples/omega_vla_r03_wave4_counterexample_demo.py

pytest -q tests/test_omega_vla_r03_wave4.py
python -m omega_vla_t.r03.wave4.cli oak
```
