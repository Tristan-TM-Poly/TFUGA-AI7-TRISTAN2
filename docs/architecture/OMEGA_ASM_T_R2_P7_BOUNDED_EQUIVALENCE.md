# Ω-ASM-T∞ R2 — P7 Bounded Equivalence Laboratory

**Status:** stacked on P6.  
**Authority:** `review_only`.  
**Kernel-checked:** **no** in this R2 slice.

## Mission

P7 adds a formal-semantics boundary around finite assembly-style rewrites without pretending that a solver transcript or a small test suite proves arbitrary source-code equivalence.

The R2 P7 object is a fixed-width bit-vector equivalence problem:

```text
forall variables in BV(width): lhs == rhs
```

The generated SMT obligation asks for the opposite:

```text
exists variables in BV(width): lhs != rhs
```

Therefore an SMT `unsat` result means no counterexample exists **for the encoded fixed-width bit-vector statement**.

## Supported expression language

R2 supports a deliberately small total language:

```text
var
const
not
neg
add
sub
mul
xor
and
or
shl
lshr
```

Widths are integers from 1 through 64.

Every arithmetic operation uses modulo `2^width` semantics. Constants are normalized to the same domain.

This is close to useful machine-integer reasoning, but it is not automatically the semantics of C/C++/Rust source programs.

## JSON expression form

Variable:

```json
{"op":"var","name":"x"}
```

Constant:

```json
{"op":"const","value":2}
```

Binary expression:

```json
{
  "op":"add",
  "args":[
    {"op":"var","name":"x"},
    {"op":"var","name":"y"}
  ]
}
```

Equivalence specification:

```json
{
  "name":"add-commutativity",
  "width":8,
  "lhs":{"op":"add","args":[{"op":"var","name":"x"},{"op":"var","name":"y"}]},
  "rhs":{"op":"add","args":[{"op":"var","name":"y"},{"op":"var","name":"x"}]}
}
```

## Obligation compiler

`build_equivalence_obligation()` normalizes the AST and emits:

```text
obligation_id = SHA256(canonical normalized statement)
logic = QF_BV
declarations for all variables
assert(not(lhs == rhs))
check-sat
```

The obligation records:

```text
evidence_level = P7-bounded-equivalence-obligation
claim_scope = this_normalized_bitvector_statement_only
semantics = fixed_width_unsigned_bitvector_modulo_2^width
```

CLI:

```bash
omega-asm p7-obligation spec.json --output obligation.json
```

The JSON contains the replayable SMT-LIB2 program in `smt2`.

## Exhaustive finite verifier

For sufficiently small finite domains, `exhaustive_verify()` checks every assignment.

If there are `n` variables of width `w`:

```text
states_total = (2^w)^n
```

Default budget:

```text
max_states = 1,000,000
```

Possible results:

### `equivalent`
Every state was checked and lhs == rhs for all of them.

### `counterexample`
A concrete assignment was found with distinct lhs/rhs values.

### `not_run`
The full state space exceeds the configured budget. No partial search is misrepresented as exhaustive proof.

## External solver separation

The package does **not** execute Z3 or another solver.

```text
omega-asm
  -> generates SMT obligation
external controlled verifier
  -> produces sat / unsat / unknown transcript
omega-asm
  -> ingests transcript as evidence
```

This preserves generation/verification separation and prevents the package from exposing a generic subprocess/solver-execution surface.

A raw text file containing `unsat` can be forged, so **solver text alone does not grant acceptance** in R2.

## Certificate statuses

### `dual_verified_bounded`
Complete exhaustive enumeration says equivalent and external solver evidence says `unsat`.

`accepted_equivalent = true`.

### `exhaustive_verified_bounded`
Complete exhaustive enumeration says equivalent, without independent solver `unsat` evidence.

`accepted_equivalent = true`.

### `solver_unsat_observed`
Full exhaustive enumeration was not run, and an external transcript says `unsat`.

`accepted_equivalent = false` in R2 because transcript ingestion is not itself an independently checked solver proof object.

### `solver_sat_observed`
Solver says `sat`, but exhaustive verification was not complete.

Not accepted.

### `refuted_exhaustive`
A concrete exhaustive counterexample exists.

Not accepted.

### `evidence_conflict`
Solver and exhaustive evidence disagree.

Not accepted and should be escalated into M−.

### `unverified`
No complete accepted evidence exists.

## Negative court

The CI must test both a true and a false statement.

Positive example:

```text
(x + y) mod 2^w == (y + x) mod 2^w
```

Negative example:

```text
(x + y) mod 2^w == x XOR y
```

The negative expression must produce a real counterexample rather than merely failing a positive assertion.

This is essential: a proof system that only tests statements expected to succeed is not adequately falsified.

## Solver court

The controlled GitHub workflow may install Z3 and independently replay the generated QF_BV obligation.

The workflow:

1. asks `omega-asm` to generate the obligation;
2. extracts the SMT-LIB2 text;
3. asks Z3 externally for `sat/unsat/unknown`;
4. stores solver version and transcript;
5. passes that transcript back to `omega-asm p7-certificate`;
6. independently requires exhaustive coverage for the small CI statement;
7. validates the resulting JSON schema.

The package itself still does not invoke Z3.

## Why `kernel_checked = false`

Even when exhaustive enumeration is complete, the verifier is ordinary project code rather than an independently minimized proof kernel. Even when Z3 agrees, the current certificate stores solver status/transcript hash rather than an independently replayable proof object checked by a second kernel.

Therefore R2 always records:

```text
kernel_checked = false
```

Future promotion can add:

- proof-producing SMT with independently checkable proof objects;
- Alethe/LFSC/DRAT-style certificate paths where applicable;
- Lean/Rocq/Isabelle bridges for selected rewrite theorems;
- translation validation from machine instruction semantics to the bit-vector AST.

## Important semantic boundary

This P7 layer does **not** automatically prove source-language rewrites.

For example, unsigned bit-vector addition corresponds naturally to modulo arithmetic, while signed C/C++ overflow can invoke language rules that differ from pure modulo bit vectors.

Before applying a P7 result to source code, a separate semantics bridge must state exactly which language types, compiler assumptions and undefined/implementation-defined behaviors are modeled.

## P7 is not performance evidence

A rewrite can be formally equivalent and slower.

Therefore:

```text
P7 correctness evidence != P4 timing
P7 correctness evidence != P5 counters
P7 correctness evidence != P6 replication
```

The optimizer must combine them only after preserving their independent provenance.

## CLI

```bash
omega-asm p7-obligation spec.json
omega-asm p7-certificate spec.json
omega-asm p7-certificate spec.json \
  --solver-result z3.txt \
  --solver-name z3 \
  --solver-version "4.x" \
  --max-states 1000000
```

## M− / anti-claims

- Solver transcript text alone is not accepted proof evidence.
- Bounded width does not imply unbounded integer truth.
- Bit-vector equivalence does not automatically preserve C/C++ undefined behavior.
- Exhaustive enumeration beyond the declared budget is not silently sampled.
- A counterexample always defeats acceptance.
- Conflicting independent evidence never resolves by majority vote.
- Formal equivalence does not imply performance improvement.
- Formal evidence never grants automatic merge or publication authority.

## Next formal step

The strongest continuation is a **translation-validation layer**:

```text
trusted built-in ASM instruction window
-> machine-semantics AST
-> bit-vector obligation
-> solver / exhaustive verifier
-> certificate
-> exact source+binary+disassembly provenance
```

That turns P7 from an algebra laboratory into proof-carrying assembly optimization while maintaining explicit semantic scope.
