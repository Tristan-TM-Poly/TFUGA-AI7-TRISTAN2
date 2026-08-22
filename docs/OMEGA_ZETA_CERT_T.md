# Ω-ZETA-CERT-T∞ R0.2 — Proof-Frontier & Spectral Certificate Compiler

## Mission

R0.2 turns Ω-ZETA-CERT-T∞ from a bound/frontier classifier into a bounded **proof-frontier compiler**.

```text
external reported theorem family
→ exact epistemic scope
→ target bound
→ moment-word representation
→ support debt
→ theorem obligations
→ exact countermodels
→ finite dual-certificate kernel
→ formal theorem specification
→ Bayes-Tristan/VOI routing
→ R0.10 Problem Atlas cells
→ OAK
```

The system still makes **no claim to prove the Riemann Hypothesis**.

## External 2026 seed

The repository stores the following as external-reported inputs:

```text
reported optimized critical-line lower bound = 0.6725
declared family ceiling                     = 0.6818
declared Fourier-support radius             = 1
```

For a research target of `0.70`, R0.2 therefore emits:

```text
new_arithmetic_information_required
```

This is a research barrier classification, not a theorem about what every possible method can or cannot achieve.

## 1. Noncommutative moment-word correction

R0.1 used a fully symmetrized cross-moment count. For three windows through order four this gives:

```text
3 + 6 + 10 + 15 = 34
```

That quotient is valid only if the required permutation symmetry has actually been justified.

For noncommuting operators, trace gives cyclic invariance:

```text
tr(A1 A2 ... Ak) = tr(A2 ... Ak A1)
```

but not arbitrary permutation invariance in general.

R0.2 therefore introduces `MomentWordMode`:

- `diagonal_only`
- `fully_symmetrized`
- `cyclic_trace_words`
- `full_noncommutative_words`

The default research bundle now uses `cyclic_trace_words`.

For `W=3`, the exact cyclic-word counts are the necklace numbers:

```text
order 1:  3
order 2:  6
order 3: 11
order 4: 24
----------------
total:   44
```

The full noncommutative word count is:

```text
3 + 9 + 27 + 81 = 120
```

Therefore R0.2 records the hierarchy:

```text
34  fully symmetrized
44  cyclic trace quotient
120 full words
```

and refuses to silently move from 44 to 34 without an extra theorem.

## 2. Exact M− countermodel to unjustified symmetrization

R0.2 contains an exact dependency-free 2×2 matrix court.

Let

```text
A = E12
B = E21
C = E11
```

Then exactly:

```text
tr(ABC) = 1
tr(BCA) = 1
tr(CAB) = 1
tr(ACB) = 0
```

Hence cyclic trace invariance holds while arbitrary permutation invariance fails.

Permanent M−:

```text
full_symmetrization_of_noncommutative_trace_words_without_extra_theorem
```

This is a software/mathematical counterexample to an invalid compression rule. It is not a statement about a particular zeta operator until the relevant operator model has been derived.

## 3. Ω-SUPPORT-DEBT-ALGEBRA-T

Every requested moment order receives a conservative support-debt record.

If one base window has bookkeeping radius `b`, the order-`k` conservative Minkowski bound is:

```text
k * b
```

For the default `b=1`, `K=4` bundle:

```text
order 1 -> radius 1
order 2 -> radius 2
order 3 -> radius 3
order 4 -> radius 4
```

This is deliberately labelled:

```text
conservative_minkowski_bookkeeping_not_arithmetic_theorem
```

It does **not** assert that a zeta prime-side moment actually requires the entire conservative radius, nor that estimates in that range exist. Its purpose is to prevent a generated higher-moment proposal from hiding its information debt.

## 4. Ω-THEOREM-DEBT-COMPILER-T

For a target, family and representation, R0.2 derives explicit theorem obligations.

For the default target `0.70`, the current obligations include:

### Cross the declared family ceiling

```text
zeta-cross-declared-family-ceiling
```

Minimal requirement: prove an arithmetic estimate, moment identity, support extension, or alternative certificate input outside the declared family.

### Discharge support debt

```text
zeta-discharge-support-debt
```

Every promoted moment must eventually receive its exact prime-side identity and true information range.

### Preserve noncommutative information

```text
zeta-no-unjustified-full-symmetrization
```

Cyclic trace words may not be identified under arbitrary permutations without a commutation/adjoint/symmetry theorem.

### Polynomial-dual domain control

```text
zeta-polynomial-dual-domain-control
```

Any future global interval-polynomial certificate needs a proved spectral-domain bound or an appropriate tail-control replacement.

This converts:

```text
Can we reach 70%?
```

into:

```text
What is the smallest exact mathematical obligation that must be discharged before a 70% certificate can be promoted?
```

## 5. Exact finite spectral dual kernel

R0.2 adds a dependency-free exact rational kernel for an abstract certificate pattern.

Let `mu` be a normalized positive spectral measure supported in `[-L,L]`. Suppose a polynomial `p` satisfies:

```text
p(x) <= 0  on [-L,0]
p(x) <= 1  on [0,L]
```

Then:

```text
mu((0,+infinity)) >= integral p dmu.
```

If exact normalized moments `m_k` are known and

```text
p(x) = sum a_k x^k,
```

then:

```text
integral p dmu = sum a_k m_k.
```

### Exact interval verification

R0.2 does not validate these inequalities by a floating-point grid. It transforms the polynomial into the Bernstein basis on each interval using exact `fractions.Fraction` arithmetic.

If every Bernstein coefficient of `-p` on `[-L,0]` is nonnegative, that is a sufficient exact certificate for `p<=0` there. If every Bernstein coefficient of `1-p` on `[0,L]` is nonnegative, that is a sufficient exact certificate for `p<=1` there.

This condition is sufficient, not necessary. A valid polynomial can fail the Bernstein sufficient test and therefore be rejected conservatively.

## 6. Synthetic exact dual fixture

The reference fixture uses exact spectrum:

```text
(-1, 1, 1)
```

with normalized moments:

```text
m0 = 1
m1 = 1/3
```

and polynomial:

```text
p(x) = x
```

on `[-1,1]`.

R0.2 exactly verifies the polynomial inequalities and obtains:

```text
certified lower bound = 1/3
```

The actual positive spectral mass of the fixture is `2/3`. This intentionally preserves:

```text
certificate validity != certificate optimality
```

The fixture is classified:

```text
synthetic_exact_kernel_test_not_zeta_evidence
```

## 7. Fail-closed spectral-domain gate

The same polynomial and moments are **not** allowed to produce a certified lower bound when:

```text
domain_control_proven = false
```

This encodes:

```text
nice polynomial + moments != global spectral certificate
```

without a theorem controlling the domain/tails on which the polynomial inequalities are required.

For zeta, R0.2 therefore records the domain-control question as theorem debt rather than inventing an operator norm.

## 8. Ω-THEOREM-SHADOW-PRICE-T interface

R0.2 adds `DualSensitivity`. It accepts a caller-supplied dual multiplier:

```text
observable_id
dual_multiplier
anticipated_observable_improvement
theorem_cost
source_class
```

and computes:

```text
shadow_value = |dual_multiplier| * |anticipated improvement|
theorem_voi  = shadow_value / declared theorem cost
```

The system never invents its own dual multiplier. The score is labelled:

```text
sensitivity_per_declared_cost_not_truth_probability
```

This creates the interface needed for a future SDP/SOS backend while keeping R0.2 dependency-free and epistemically conservative.

## 9. Formal theorem-spec bridge

The exact finite dual fixture can be compiled into a typed theorem specification targeting:

```text
Lean4/mathlib
```

The object contains theorem ID, assumptions, exact conclusion, source scope, and backend target. It also contains:

```text
status         = theorem_spec_only
kernel_checked = false
proof_claimed  = false
```

R0.2 therefore separates:

```text
theorem specification
!= Lean source
!= kernel-checked proof
!= zeta adapter proof
```

## 10. Problem Atlas R0.10 integration

The generated research cells use exactly:

```text
schema     = omega-problem-stream-cell/10
problem_id = riemann
```

R0.2 fronts include:

```text
barrier
representation
support-debt
theorem-debt
countermodel
verification-fixture
formal-obligation
research-route
m-minus
```

Every row must round-trip through the existing `omega_millennium_t.r10.model.CellRecord` parser. The default target currently produces 21 deterministic cells.

## 11. Commands

```bash
python -m omega_zeta_cert_t frontier --target 0.70
python -m omega_zeta_cert_t routes --target 0.70
python -m omega_zeta_cert_t moments
python -m omega_zeta_cert_t moments --labels
python -m omega_zeta_cert_t debt --target 0.70
python -m omega_zeta_cert_t countermodel
python -m omega_zeta_cert_t dual-fixture
python -m omega_zeta_cert_t formal-spec
python -m omega_zeta_cert_t shadow-voi \
  --observable 'M4:cyc[0,1,0,2]' \
  --multiplier -2 \
  --delta 0.03 \
  --cost 0.2 \
  --source-class synthetic_dual_fixture
python -m omega_zeta_cert_t cells --target 0.70 --output /tmp/zeta_r02.jsonl
```

## 12. Research architecture after R0.2

```text
TARGET
  ↓
CERTIFICATE FAMILY
  ↓
MOMENT WORD ALGEBRA
  ↓
SUPPORT DEBT
  ↓
THEOREM DEBT
  ↓
COUNTERMODEL COURT
  ↓
FINITE EXACT CERTIFICATE KERNEL
  ↓
DUAL SENSITIVITY / THEOREM VOI
  ↓
FORMAL THEOREM SPEC
  ↓
ZETA ANALYTIC ADAPTER [future]
  ↓
LEAN KERNEL PROOF [future]
```

## 13. R0.3 frontier

Priority order:

1. independently reconstruct the external 2026 paper constants and exact method-ceiling statement;
2. create an exact equation/provenance ledger for every external numerical constant;
3. compile actual moment candidates into symbolic prime-side obligations;
4. add a solver-independent dual-certificate JSON contract;
5. attach independent LP/SOS/SDP backends as proposal generators;
6. rationalize candidate certificates before promotion;
7. formalize the finite abstract certificate theorem in Lean;
8. create a zeta explicit-formula adapter;
9. add analogue/countermodel families;
10. only then evaluate whether any new moment/input actually improves the certified zeta bound.

## OAK invariants

```text
external reported value != independent reconstruction
method ceiling != universal mathematical impossibility
44 cyclic words != proof those observables are analytically available
support bookkeeping != prime-correlation theorem
exact synthetic certificate != zeta theorem
theorem spec != kernel proof
dual multiplier supplied by optimizer != probability of truth
CI green != mathematical truth
formal proof of abstract kernel != proof that zeta satisfies its assumptions
fractal/orbit pattern != RH evidence by itself
```

No RH proof, Millennium solution, publication claim, prize claim, or automatic merge is authorized by this module.
