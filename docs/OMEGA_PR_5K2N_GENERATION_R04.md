# Ω-PR-5K2N-T∞ R0.4 — Exact Hydration + Compatibility Experiment Compiler

## Objective

R0.3 deliberately stops at `INSPECT` when prior PR candidates exist but no explicit artifact Capability contract proves reuse. R0.4 makes that inspection executable without silently upgrading static similarity into compatibility.

```text
R0.3 INSPECT queue
-> exact historical PR ref
-> hydrate exact PR metadata + changed files
-> fetch Python source at candidate head SHA
-> static AST symbol extraction
-> test/workflow surface inventory
-> exact-head freshness check
-> CompatibilityInspectionReceipt
-> CompatibilityExperimentContract
```

## Reused kernel

R0.4 reuses `ProgressiveGitHubRetriever` from the cumulative-memory stack. It does not create a second GitHub fetcher or a parallel AST ontology.

Hydration can observe:

- candidate PR head SHA;
- changed file paths;
- Python source at that head;
- static classes/functions/methods;
- test file paths;
- workflow file paths.

Candidate code is not imported or executed during hydration.

## Exact-head rule

The R0.3 plan retains the candidate head SHA observed in historical memory. R0.4 compares this with the hydrated head.

```text
planned SHA == hydrated SHA
-> HYDRATED_EXACT_HEAD

planned SHA != hydrated SHA
-> STALE_HEAD
-> no experiment contract
```

If either SHA is unavailable, the state remains `HYDRATED_HEAD_UNVERIFIED` and is not promoted to an executable experiment contract.

## Static evidence classes

R0.4 distinguishes:

```text
UNHYDRATED
METADATA_ONLY
STATIC_ONLY
STATIC_SOURCE_TEST_SURFACE
STATIC_SOURCE_TEST_CI_SURFACE
STALE_EVIDENCE
```

These labels describe only the observable repository surface.

```text
workflow file exists != workflow passed

test file exists != test passed

symbol exists != behavior compatible
```

## Compatibility verdict

Every R0.4 static receipt intentionally emits:

```text
compatibility_verdict = UNKNOWN
compatibility_proven = false
reuse_authorized = false
execution_authorized = false
```

Even an exact-head candidate with source, tests, workflows and symbol overlap is still only a better experiment target.

## CompatibilityExperimentContract

An exact-head hydrated candidate may produce a test obligation containing:

- candidate PR/ref and exact head SHA;
- target PR/ref and exact head SHA;
- declared artifact residual outputs;
- candidate source files;
- candidate test files;
- required interface/behavior checks;
- expected evidence fields;
- explicit non-authority flags.

Permanent R0.4 state:

```text
execution_authorized = false
source_mutation_authorized = false
reuse_authorized_before_experiment = false
human_review_required = true
```

The intended R0.5 transition is:

```text
CompatibilityExperimentContract
-> separately authorized isolated test execution
-> evidence-bearing CompatibilityOutcomeReceipt
-> COMPATIBLE / INCOMPATIBLE / UNKNOWN
-> REUSE / EXTEND / M- / HOLD
```

## Target path overlap

R0.4 records exact changed-path overlap when target changed files are known. This is a strong structural clue but still not semantic equivalence.

It also records a bounded lexical intent-overlap proxy between target genome tokens and candidate PR keywords. This remains retrieval/inspection evidence only.

## Why no source renderer yet

R0.4 deliberately refuses the tempting step:

```text
exact hydration -> copy code
```

The safe chain is instead:

```text
exact hydration
-> inspect
-> test compatibility
-> evidence
-> review
-> only then optional renderer
```

This prevents historical code from being transplanted solely because it shares paths, symbols, terminology or green-looking repository structure.

## OAK boundaries

```text
hydrated exact head != compatible behavior
changed-file overlap != semantic equivalence
AST symbol overlap != interface compatibility
test file exists != test passed
workflow file exists != CI passed at candidate head
intent overlap proxy != reuse proof
CompatibilityExperimentContract != experiment execution
no R0.4 static receipt authorizes reuse
candidate head drift invalidates exact-head inspection evidence
CI green for this compiler != compatibility of candidate code
```

## R0.5 frontier

The next useful generation is empirical compatibility, not a larger virtual forest:

1. execute bounded target-specific compatibility experiments in isolation;
2. pin candidate/target SHAs and dependency environment;
3. require exact test commands and results;
4. collect interface/behavior mismatches and regression witnesses;
5. produce `CompatibilityOutcomeReceipt` with evidence refs;
6. classify compatible/incompatible/unknown without collapsing uncertainty;
7. feed failures into M− only when evidence-bearing;
8. benchmark reuse-first versus create-first physical cost;
9. authorize source rendering only through a separate explicit write decision.
