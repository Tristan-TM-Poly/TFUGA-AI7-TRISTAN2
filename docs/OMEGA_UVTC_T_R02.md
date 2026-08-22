# Ω-UVTC-T∞ R0.2 — Typed Semantics, GO Certificates, Artifacts and Pareto Control

R0.2 extends the compact R0.1 UTIR-16 ABI without replacing the already-merged Discovery OS, Cognitive Computer or Capability OS.

## Mother pipeline

```text
Intent
→ R0.1 UTIR-16
→ GO MAX / GO MIN superoptimizer
→ structural preservation certificate
→ abstract operational semantics
→ evidence obligations
→ GOArtifact / ReproCapsule contract
→ KnowledgeMake
→ residual feedback
→ finite Pareto GO selection
```

The R0.1 semantic ISA stays stable. R0.2 adds interpretation, validation and selection layers around it.

## 1. Abstract Science Virtual Machine

`omega_uvtc_t.semantics` gives UTIR a deterministic state-transition semantics. It checks ordering constraints such as:

- `STATE` before `GOAL`;
- `GOAL + SEARCH` before transformation-family instructions;
- transformation before `MEASURE`;
- `MEASURE` before `FALSIFY`;
- `MEASURE + FALSIFY` before `OAK`;
- `OAK` before `MEMORIZE`, `RESIDUAL` and `CRYSTALLIZE`;
- `MEMORIZE` before `LEARN_PRIMITIVE`.

The SVM records obligations. Visiting `PROVE`, `MEASURE`, `FALSIFY`, `OAK` or `CRYSTALLIZE` never fabricates completion evidence.

## 2. GO MIN structural certificates

`omega_uvtc_t.certificates` verifies that a superoptimization preserves three explicit traces:

1. protected evidence/crystallization primitives;
2. the multiset of independent-replication instructions;
3. instructions carrying non-elidable effects.

A certificate `PASS` means these finite structural invariants survived the rewrite. It explicitly sets:

```text
semantic_equivalence_proven = false
```

General semantic equivalence is not claimed.

## 3. GOArtifact + ReproCapsule

`omega_uvtc_t.artifact` separates the validation dimensions of a crystallized artifact:

```text
integrity
reproducibility
empirical_support
formal_validity
calibration
```

`ReproCapsule` binds environment, input hashes, dependency hashes, replay-step descriptors and expected output hashes into a deterministic fingerprint.

A reproducibility PASS without a capsule is rejected.

A content hash proves identity/integrity of declared bytes; it does not prove scientific truth.

## 4. GO MAX / MIN finite Pareto compiler

`omega_uvtc_t.portfolio` keeps the optimization multi-objective.

Maximized axes:

```text
verified value
reachability
evidence gain
reuse
leverage
```

Minimized axes:

```text
cost
risk
duplication
proof debt
uncertainty debt
complexity
```

`pareto_front()` computes the exact non-dominated frontier over the supplied finite candidate set. `select_go_move()` then uses Power Density only inside that frontier and implements a bounded recursion stop rule.

This is exact only for the supplied finite candidates and proxy axes, not a global optimum over all possible transformations.

## 5. Generalized Residual Genome

R0.2 generalizes residuals beyond a single Euclidean orthogonal error:

```text
numeric
logical
causal
structural
semantic
experimental
```

Residuals remain typed observations. Their uncertainty-aware ranking is a research-priority proxy, not proof of causal importance.

## 6. Vertical pipeline receipt

`omega_uvtc_t.pipeline.run_pipeline()` performs:

```text
compile
→ superoptimize
→ certify_optimization
→ execute_abstract
→ UVTCPipelineReceipt
```

The receipt contains source/optimized fingerprints, optimization event count, certificate status, operational status and unresolved evidence obligations.

A pipeline PASS is a deterministic local software-contract result only.

## Deterministic court

R0.2 adds 10 focused tests on top of the 7 R0.1 tests. The pre-publication local court passed all 17 UVTC tests.

Coverage includes:

- valid and invalid operational ordering;
- obligation preservation;
- independent-replication preservation;
- structural optimization certificate;
- ReproCapsule requirement;
- finite Pareto dominance;
- GO continuation/stop rule;
- generalized residual priority;
- SCC-aware KnowledgeMake regression;
- deterministic full R0.2 pipeline.

## OAK boundaries

```text
UTIR instruction != completed action
PROVE instruction != proof
MEASURE instruction != measurement
OAK instruction != truth
structural certificate != semantic equivalence
hash identity != truth
reproducibility != correctness
Pareto frontier != global optimum
Power Density != natural constant
residual priority != causal importance
pipeline PASS != external scientific validation
```

## Next evidence frontier

The next useful increment is evidence integration rather than primitive proliferation:

1. cross-check acyclic KnowledgeMake invalidation against the merged Discovery OS `ScientificBuildGraph`;
2. bind real Capability OS receipts into satisfied/unsatisfied SVM obligations;
3. attach formal-proof receipts without conflating them with empirical support;
4. benchmark optimizer savings against an unoptimized UTIR baseline;
5. measure learned macro-instructions before promotion into any MacroISA registry;
6. add a dedicated repository CI workflow when the connected write surface permits it.
