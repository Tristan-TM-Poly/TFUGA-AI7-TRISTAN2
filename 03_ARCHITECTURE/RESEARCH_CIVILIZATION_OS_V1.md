# Research Civilization OS v1 — Architecture

## Dataflow

```text
Question / Residual
       |
       v
MorphogenesisKernel.rank_residuals
       |
       v
ResearchCivilizationKernel.compile
       |
       +--> irreducible cell: Generator + Falsifier + Verifier
       +--> JIT solver if justified
       +--> lazy institution/simulation candidates if complexity warrants
       |
       v
CivilizationPlan
       |
       +--> materialize(candidate) -- finite gain/depth/budget gate
       +--> judge_claim(claim) ----- provenance/independence/epistemic gate
       +--> prune(...) ------------- cognitive apoptosis
       |
       v
Distill verified claims + materialized blueprints
       |
       v
ResearchSeed (BOOK0-like)
       |
       v
regenerate(seed) -> CivilizationPlan
       |
       v
regeneration_closure
```

## Why this is a specialization, not a competing kernel

`omega_research_civilization` imports and reuses `omega_morphogenesis` for residual ranking, evidence status, and regeneration closure. It does not replicate the repository's general authority/epistemic morphogenesis court.

## Finite recursion

No recursive call creates an infinite tree. `max_depth`, `max_materialized_units`, parent materialization, and positive spawn margin are hard structural gates. A virtual university is a generated organizational candidate, not a mandatory parent of every agent.

## Identity separation

Claims carry three identities: producer, falsifier, verifier. This is deliberately stricter than a single generator/verifier split for scientific promotion. Identity strings are an architectural contract only; production deployments should map them to independently isolated processes/models/people where appropriate.

## Failure containment

- malformed seed -> reject;
- duplicate unit IDs -> reject;
- missing parent -> reject;
- missing generator/falsifier/verifier role -> reject;
- depth above seed policy -> reject;
- materialization budget overflow -> reject;
- simulation-only evidence -> do not persist as verified claim;
- epistemic inflation -> reject claim promotion.

## Evolution path

V2 should add a representation tournament, heterogeneous verifier ecology, explicit experiment contracts, solver topology search, real benchmark traces, capability contracts across federated virtual universities, and mutation tests against the scientific constitution. New features should be promoted only when they beat a frozen v1 baseline on out-of-sample tasks.
