# Ω-TRISTAN-OMNIUNIVERSITY-SELFGENESIS-T∞ — R0.1

Status: **X/D-candidate** — executable seed, not an accredited institution, pedagogical superiority proof, credentialing authority, or scientific validation.

## Mission

Crystallize the virtual-university theory into the smallest reusable kernel that can compile a declared capability goal into a deterministic, inspectable learning dependency plan.

```text
Goal
→ Capability targets
→ Verified capabilities
→ Prerequisite graph
→ CurriculumCompiler
→ CurriculumPlan
→ Receipt
→ OAK / external evaluation
```

The R0.1 kernel deliberately does **not** generate lessons, grade people, award credentials, infer hidden traits, mutate external systems, or claim that a dependency plan causally teaches anything.

## Core object

The primitive is a `VerifiedCapabilityTransformation`, not a course or degree. R0.1 only compiles the dependency side of that transformation:

```text
CapabilityGoal != CurriculumPlan
CurriculumPlan != Learning
Learning != VerifiedCapability
VerifiedCapability != Credential
Credential != HumanValue
Generated != Verified
Simulation != Reality
```

## Files

- `university_ir.py` — deterministic stdlib-only curriculum dependency compiler and receipt builder;
- `BOOK0.json` — minimal regenerative seed and invariants;
- `schema/curriculum_plan.schema.json` — machine-readable plan contract;
- `tests/test_university_ir.py` — focused OAK court;
- `OAK_RECEIPT_R0_1.md` — claim scope, limits, and promotion gates;
- `.github/workflows/omega-university-r01.yml` — isolated Python 3.10–3.13 CI.

## R0.1 semantics

Given:

- a finite directed prerequisite graph;
- one or more target capabilities;
- a set of already verified capabilities;

`compile_curriculum()` returns a deterministic topological plan containing only missing reachable capabilities. Verified capabilities cut dependency expansion because R0.1 treats the caller-supplied verification state as an explicit input assumption.

The compiler fails closed on:

- empty target sets;
- unknown targets;
- unresolved prerequisite references;
- cycles in the reachable missing-capability graph.

## Why this is intentionally small

The larger theory includes adaptive tutors, JIT faculties, research-frontier routing, cognitive debugging, proof-carrying credentials, federated institutions, reality arenas, M+/M-/Forget+, curriculum CI and self-distillation. R0.1 does not pretend those exist merely because they have names.

The first falsifiable question is smaller:

> Can the repository represent and deterministically compile a capability dependency graph without confusing planning with teaching, authority, proof, or credentialing?

## Next discriminating experiments

1. compare compiled dependency plans with human-authored baselines on small curricula;
2. add explicit evidence requirements and expiry without creating a global person score;
3. measure plan ablations and prerequisite necessity on synthetic fixtures before empirical pedagogical claims;
4. connect existing OAK / capability / intent contracts only through narrow adapters;
5. add research-frontier routing only after the capability kernel has independent evaluation.

## Promotion rule

Promote beyond R0.1 only if exact-head CI passes and a later empirical court measures learning/transfer outcomes against a baseline. Repository tests can validate software behavior; they cannot establish educational effectiveness.
