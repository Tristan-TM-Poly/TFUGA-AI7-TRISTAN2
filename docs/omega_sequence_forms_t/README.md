# Ω-SUITE-FORM-T∞ — R0.1

Exact, OAK-safe discovery of analytic representations for finite mathematical
sequence prefixes.

## Epistemic status

This package is research software.  Given finitely many terms, infinitely many
infinite sequences remain compatible with the observations.  Therefore R0.1
never promotes a fitted formula to a global theorem.  It distinguishes:

1. observed-prefix fit;
2. held-out prediction;
3. independent generator checks;
4. symbolic identity;
5. mathematical proof;
6. formal proof.

Only the first two levels are produced automatically by the current engine.

## Implemented representation hypergraph

R0.1 discovers and links three representation nodes:

```text
finite prefix
  ├─ forward-difference tower
  │    └─ Newton polynomial in binomial basis
  └─ exact Hankel-style recurrence search
       ├─ minimal constant-coefficient recurrence
       └─ rational ordinary generating function
```

### Newton polynomial

For coefficients `c[k] = Δ^k a[0]`, the candidate is

```text
a[n] = Σ c[k] binom(n,k).
```

A degree is accepted only when the corresponding difference row has at least
two equal entries.  The vacuous degree `N` polynomial interpolating `N+1`
points is deliberately rejected.

### Linear recurrence

R0.1 searches the smallest order `r` satisfying

```text
a[n] = c[0]a[n-1] + ... + c[r-1]a[n-r].
```

The coefficient system is solved by exact rational Gauss-Jordan elimination.
Underdetermined and inconsistent systems are rejected.

### Rational generating function

Every accepted recurrence is compiled into

```text
A(z) = P(z) / Q(z),
Q(z) = 1 - c[0]z - ... - c[r-1]z^r.
```

The numerator is reconstructed from the initial values.  This generating
function is exact conditional on the inferred recurrence; it is not an
unconditional proof that the observed sequence continues by that recurrence.

## CLI

```bash
python -m omega_sequence_forms_t.cli discover "0,1,1,2,3,5,8,13,21,34,55,89"
python -m omega_sequence_forms_t.cli demo fibonacci
python -m omega_sequence_forms_t.cli benchmark
```

After package installation:

```bash
omega-sequence-forms discover "1,8,27,64,125,216,343,512,729"
```

The JSON report contains:

- exact terms;
- training/holdout split;
- candidate formulas;
- exact parameters;
- validation counts;
- OAK evidence level;
- deterministic complexity score;
- difference and ratio diagnostics;
- warnings against finite-prefix overclaiming.

## Python API

```python
from omega_sequence_forms_t import CandidateKind, discover_forms

report = discover_forms([0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89])

for candidate in report.candidates:
    print(candidate.kind, candidate.expression, candidate.oak_level)

recurrence = next(
    candidate
    for candidate in report.candidates
    if candidate.kind == CandidateKind.LINEAR_RECURRENCE
)
assert recurrence.evaluate(12) == 144
```

## OAKBench R0.1

The test suite verifies:

- exact overdetermined linear algebra;
- cubic finite differences;
- Newton-polynomial discovery;
- Fibonacci recurrence discovery;
- recurrence-to-generating-function compilation;
- exact extrapolation;
- rejection of vacuous interpolation;
- demotion of a formula that fails held-out terms;
- deterministic JSON output;
- explicit `global_identity_proved: false` receipts.

## Current limits

R0.1 does not yet infer:

- P-recursive or Ore-algebra recurrences;
- hypergeometric ratios;
- algebraic or D-finite generating functions beyond the rational case;
- quasi-polynomials and modular branches;
- moment/integral forms;
- asymptotic expansions or transseries;
- nonlinear recurrences through tensor lifting;
- proof certificates from a supplied generator or definition.

These are planned as independent petals sharing the same typed candidate,
validation, evidence and negative-memory interfaces.

## R0.2 roadmap

1. rational-ratio interpolation for hypergeometric terms;
2. modular/quasi-polynomial decomposition;
3. exact Hankel rank diagnostics and Prony spectral form;
4. polynomial-coefficient recurrence guessing;
5. symbolic certificate hooks;
6. adversarial competing-continuation generator;
7. representation-hypergraph export;
8. OEIS-style corpus benchmark without treating database matches as proofs.

## OAK invariant

> A formula inferred from a finite prefix is a candidate mechanism.  It becomes
> a theorem only after a valid global argument, not after a large numerical fit.
