# Ω-REPRESENTATION-NOETHER-COMPILER-T∞ — R0.5

## Status

**Executable software model / benchmark contract.**

R0.5 does not claim a physical conservation law, a theorem about cognition, a
historical law of discovery, or scientific superiority of any representation.
It provides an auditable software calculus for comparing declared
representation transformations under declared metrics.

## Core object

A representation morphism is:

```text
RepresentationBundle A
  -- morphism -->
RepresentationBundle B
```

with explicit:

- proxy complexity before/after;
- information before/after;
- invariant measurements and tolerances;
- residual;
- uncertainty;
- risk;
- reversibility flag;
- provenance;
- epistemic claim class.

The architectural objective is not `shortest transform wins` but:

```text
useful compression
- information loss
- invariant defect
- residual
- uncertainty
- risk
```

## Noether boundary

`Noether` is an architectural analogy to invariant search under
transformations.  For every declared invariant `I`, R0.5 measures a normalized
software defect:

```text
abs(I_target - I_source) / scale
```

and compares it against an explicit tolerance.

The result can be:

- `conserved_within_tolerance`;
- `broken`;
- `indeterminate`.

Passing this audit is **not** a proof of a physical conservation law or a
mathematical theorem.

## Complexity and information

R0.5 currently supports three metric classes:

- `benchmark_proxy`;
- `empirical_measurement`;
- `formal_property`.

The Ceres fixture uses **benchmark proxies only**. The numerical values are not
measurements of Gauss's cognition and are not universal representation
complexities.

## R0.4 bridge

R0.5 audits the representation-changing steps of a `DiscoveryPath`.

For every `PathStep` where `representation_before != representation_after`, the
compiler requires at least one matching morphism. Missing morphisms fail
closed. A changing step is promotable only when it is covered and the selected
morphism is not quarantined.

This gives the chain:

```text
DiscoveryPath
  -> representation-changing PathSteps
  -> RepresentationMorphismR05
  -> invariant / loss / residual audit
  -> OAK decision
```

## Bounded morphism search

`RepresentationCompiler` can enumerate simple representation paths up to a
bounded depth. Cycles are blocked inside a candidate path and the search is
bounded explicitly.

Candidates are ranked with quarantined paths last, then by declared utility.
This is a software policy score, not a learned law of discovery.

## Negative control

The deterministic R0.5 fixture contains an intentionally bad direct shortcut:

```text
historical_problem_statement
  -> orbit_reconstruction + residual_space
```

It has attractive nominal compression but deliberately destroys information,
breaks a declared invariant, and carries large residual/uncertainty. OAK must
quarantine it and prefer the longer admissible chain.

This encodes a permanent M- rule:

```text
M-: shorter / more compressed does not imply better.
    Compression that destroys invariants or evidence must lose.
```

## Legacy bridge

The R0.2 `RepresentationMorphism` can be migrated into the R0.5 contract with
`legacy_morphism_to_r05()`. A legacy `preserved_invariants` declaration becomes
an explicit software assertion, not retrospective scientific proof.

## Machine contract

`schemas/representation_morphism_r05.schema.json` is checked against the runtime
`ClaimClass`, `MetricKind`, `RepresentationMorphismR05` and
`InvariantMeasurement` contracts.

Schema validity proves structure only.

## OAK acceptance gates

R0.5 is promotable as a software layer only when:

1. Python 3.10–3.13 compile and targeted tests pass;
2. every R0.4 representation-changing step is covered;
3. missing morphisms fail closed;
4. broken invariants quarantine a morphism;
5. the lossy shortcut loses to the admissible multi-step path;
6. JSON schema and runtime enums remain aligned;
7. no report claims physical conservation, historical cognitive measurement,
   universal proxy metrics, or scientific superiority.

## What R0.5 enables next

R0.5 is the bridge from GreatSages history to a more general research compiler:

```text
R0.4 Discovery Path IR
  -> R0.5 Representation / Noether Compiler
  -> R0.6 Cognitive ISA + bounded program search
  -> R0.7 DiscoveryBench 2.0
```

The next layer should search over operator programs while using R0.5 as a
representation-preservation gate, rather than generating arbitrary chains of
cognitive operators.

## Permanent doctrine

```text
representation change = gain + loss + invariant residue
analogy != transfer gain
proxy metric != natural law
plus ultra = more proved, not more modules
```
