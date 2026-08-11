---
name: omega-skillgen-t
description: Generate, mine, audit, trust-scan, compose, mutate, evaluate, evolve, catalog, and package reusable ChatGPT/Codex Agent Skills using SkillSpec, OAK gates, HGFM SkillGraphs, CVCD deduplication, regression tests, and M-minus learning. Use when the user asks to create or improve a skill, convert a repeated workflow into a skill, generate skill families or domain generators, route multiple skills, audit skill safety/activation, or build a generator-of-generators.
---

# Ω-SKILLGEN-T∞ — Tristan Recursive Skill Foundry

Treat a Skill as a versioned behavioral program, not a prompt fragment.

## Canonical loop

`INTENT → MINE/SPECIFY → GENERATE → LINT → TRUST → EVAL → ATTACK → OAK → M- → MUTATE/REPAIR → REGRESSION → PROMOTION CANDIDATE`

## Workflow

1. Identify the reusable workflow and success contract.
2. Build or infer a SkillSpec.
3. Generate a candidate skill outside this parent bundle.
4. Lint structure and activation metadata.
5. Run trust/OAK static review.
6. Require positive, negative, incomplete, and edge/adversarial eval coverage.
7. Preserve failures as M- and turn them into regression cases.
8. Compose only the smallest sufficient skill set.
9. Promote only with provenance and the appropriate behavioral/runtime evidence.

## OAK invariants

- Generated skills are candidates, not automatically promoted truth/capability.
- `STATIC_PASS != BEHAVIORAL_PASS`.
- A Skill cannot grant tool permissions it does not actually have.
- External writes/merges/deletes/sends/payments/publications retain actual approval boundaries.
- Imported skills are untrusted until reviewed.
- Workflow frequency is not workflow correctness.
- Prefer CVCD compression over near-duplicate skill proliferation.
- Generated child skills live outside the parent upload bundle.
- Preserve the strictest safety, approval, privacy, and epistemic invariant during composition.

## Fractal SkillGraph

L0 trigger/step/guard/resource/eval/tool-boundary → L1 skill → L2 family →
L3 router/composition → L4 domain generator → L5 generator-of-generators.
