---
name: omega-skillgen-t
description: Generate, mine, audit, trust-scan, compose, mutate, evaluate, evolve, catalog, benchmark, and package reusable ChatGPT/Codex Agent Skills using SkillSpec, OAK gates, HGFM SkillGraphs, CVCD primitive extraction, Generator Discovery bridges, regression tests, recursive campaigns, and M-minus learning. Use when the user asks to create or improve a skill, convert repeated workflows or existing generators into skills, generate skill families or domain generators, route multiple skills, inherit benchmark contracts, audit skill safety/activation, or build a generator-of-generators.
---

# Ω-SKILLGEN-T∞ — Tristan Recursive Skill Foundry

Treat a Skill as a versioned behavioral program, not a prompt fragment.

## Canonical loop

`INTENT → MINE/SPECIFY → GENERATE → LINT → TRUST → EVAL → ATTACK → OAK → M- → MUTATE/REPAIR → REGRESSION → PROMOTION CANDIDATE`

For existing Tristan generators use the extended loop:

`GENERATOR RECORD → SKILLSPEC → BENCHMARK CONTRACTS → CVCD → SKILL CANDIDATE → OAK/EVAL → CAMPAIGN → PROMOTION LEDGER`

## Workflow

1. Identify the reusable workflow and success contract.
2. Prefer authorized execution traces or existing Generator Discovery records when they provide stronger provenance than free-form reconstruction.
3. Build or infer a SkillSpec.
4. If linked Generator Discovery benchmarks exist, inherit their expected contracts, negative controls, and OAK labels without upgrading synthetic templates into empirical evidence.
5. Run CVCD primitive extraction before proliferating a large family; share materially common workflow/invariant atoms where appropriate.
6. Generate candidate skills outside this parent bundle.
7. Lint structure and activation metadata.
8. Run trust/OAK static review.
9. Require positive, negative, incomplete, and edge/adversarial eval coverage.
10. Preserve failures as M- and turn them into regression cases.
11. Compose only the smallest sufficient skill set and preserve the strictest overlapping invariant.
12. For self-improvement, generate multiple successor candidates and compare static evidence; never auto-promote the top heuristic score.
13. Advance promotion states one evidence gate at a time; preserve rollback provenance.

## Operational commands

Core foundry:

- `python scripts/omega-skillgen generate SPEC OUT`
- `python scripts/omega-skillgen lint SKILL_DIR`
- `python scripts/omega-skillgen eval SKILL_DIR`
- `python scripts/omega-skillgen trust SKILL_DIR`
- `python scripts/omega-skillgen mine EVENTS.jsonl`
- `python scripts/omega-skillgen mine-proposals EVENTS.jsonl OUT`
- `python scripts/omega-skillgen compose NAME DESCRIPTION SPEC...`
- `python scripts/omega-skillgen domain-generator PROFILE OUT`
- `python scripts/omega-skillgen mutate SPEC STRATEGY OUT`
- `python scripts/omega-skillgen catalog ROOT --graph`

Generator Discovery / CVCD / promotion bridge:

- `python scripts/omega-skillgen-bridge generator-bridge OUT --domain DOMAIN --limit N`
- `python scripts/omega-skillgen-bridge primitives SPEC... --min-support N`
- `python scripts/omega-skillgen-bridge promotion-check BEFORE AFTER EVIDENCE.json`

Benchmark bridge:

- `python scripts/omega-skillgen-benchmark audit-atlas`
- `python scripts/omega-skillgen-benchmark enrich SPEC BENCHMARKS.jsonl OUT`

Recursive successor campaign:

- `python scripts/omega-skillgen-campaign SPEC OUT`

## OAK invariants

- Generated skills are candidates, not automatically promoted truth/capability.
- `STATIC_PASS != BEHAVIORAL_PASS`.
- A Skill cannot grant tool permissions it does not actually have.
- External writes/merges/deletes/sends/payments/publications retain actual approval boundaries.
- Imported skills are untrusted until reviewed.
- Workflow frequency is not workflow correctness.
- Catalog membership is not scientific proof.
- A linked benchmark id is not a benchmark PASS.
- Synthetic benchmark templates are not empirical evidence.
- Prefer CVCD compression over near-duplicate skill proliferation.
- Generated child skills live outside the parent upload bundle.
- Preserve the strictest safety, approval, privacy, and epistemic invariant during composition.
- Recursive campaigns may rank candidates heuristically but `auto_promotion` remains false.
- Promotion states may not skip evidence gates; backward transitions require an explicit rollback reason.
- Preserve provenance from workflow traces or GeneratorRecord/BenchmarkRecord through generated SkillSpec, evals, mutations, and promotion decisions.

## Fractal SkillGraph

- L0 — trigger / step / guard / resource / eval / tool-boundary atom.
- L1 — Skill.
- L2 — Skill family.
- L3 — router / composition.
- L4 — domain generator.
- L5 — generator-of-generators.

A node at any level may expand into its lower-level hypergraph while still participating as one node in the level above.

## Current recursive ecology

The seed ecology is composed of:

- `omega-workflow-miner-t`
- `omega-skill-evaluator-t`
- `omega-skill-evolver-t`
- `omega-skill-router-t`
- `omega-generator-of-skill-generators-t`

Use the parent foundry to regenerate or extend this ecology only through the same OAK, trust, regression, provenance, and promotion rules.
