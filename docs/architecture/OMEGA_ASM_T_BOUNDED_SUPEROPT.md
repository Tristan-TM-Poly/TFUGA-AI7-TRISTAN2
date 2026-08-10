# Ω-ASM-T∞ — Bounded Proof-First Superoptimizer

## Core rule

```text
generate rewrite
-> P7 equivalence evidence
-> only accepted candidates enter selection
-> compare structural cost
-> never infer runtime speed without P4/P5/P6
```

The superoptimizer works on the fixed-width bit-vector expression language already defined by P7. It is deliberately bounded in both candidate count and exhaustive proof-state budget.

## R2 rewrite grammar

Current local rewrite families include:

- constant folding;
- `x + 0`, `x - 0`, `x xor 0`, `x or 0`;
- `x * 1`, `x * 0`;
- `x & all_ones`;
- zero shifts;
- `x xor x`, `x - x`;
- idempotent `and/or`;
- `x + x -> x << 1`;
- multiplication by a power of two -> left shift;
- canonical commutative operand ordering;
- recursive rewrites inside subexpressions.

Rules are **candidate generators**, not trusted axioms. Every non-reflexive candidate is checked through the P7 certificate path before it can win.

## Structural cost model

R2 uses an explicit non-calibrated model:

```text
omega-asm-superopt-structural-v1
```

Example weights:

```text
var/const = 0
add/sub/xor/and/or/shift = 1
not/neg = 1
mul = 3
```

These units are not cycles, latency, throughput, energy or code bytes.

## Search

Breadth-first bounded enumeration deduplicates canonical JSON expressions.

Defaults:

```text
max_candidates = 128
max_states_per_proof = 1,000,000
```

If P7 cannot complete the finite proof inside the state budget, that candidate remains unaccepted and cannot beat the reflexive baseline.

## Example

Input:

```json
{
  "name":"mul2",
  "width":8,
  "expression":{"op":"mul","args":[{"op":"var","name":"x"},{"op":"const","value":2}]}
}
```

A candidate generator proposes:

```text
mul(x,2) -> shl(x,1)
```

P7 then checks all 256 values of `x`. Only after complete equivalence may the candidate be selected as lower structural cost.

CLI:

```bash
omega-asm superopt spec.json --max-candidates 128 --max-states 1000000
```

## Negative court

The same proof gate can test an intentionally false rewrite such as:

```text
x + y -> x xor y
```

A concrete counterexample must be produced, and the candidate remains ineligible.

## OAK boundaries

- bounded search, not infinite synthesis;
- proof-first selection;
- no generated assembly execution in the package;
- no solver subprocess in the package;
- structural cost is uncalibrated P2 evidence;
- lower cost does not imply faster runtime;
- fixed-width bit-vector equivalence does not automatically model C/C++ undefined behavior;
- no result grants merge/publication authority.

## Path toward real assembly superoptimization

The next extension is translation validation:

```text
machine instruction window
-> exact machine-semantics AST
-> bounded rewrite search
-> P7 equivalence certificate
-> backend assembly emission
-> P3 native differential test
-> P4 timing
-> P5 counters
-> P6 replicated target evidence
```

That is the bridge from this algebraic superoptimizer to proof-carrying machine-code optimization.
