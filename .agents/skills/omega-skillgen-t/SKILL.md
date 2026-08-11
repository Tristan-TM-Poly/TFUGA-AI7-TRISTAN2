---
name: omega-skillgen-t
description: Generate, mine, audit, trust-scan, compose, mutate, evaluate, evolve, catalog, benchmark, deduplicate, and package reusable ChatGPT/Codex Agent Skills using SkillSpec, OAK gates, HGFM SkillGraphs, SkillGenome, CVCD primitive extraction, Generator Discovery bridges, behavioral telemetry, recursive campaigns, regression tests, and M-plus/M-minus learning. Use when the user asks to create or improve a skill, convert repeated workflows or existing generators into skills, generate skill families or domain generators, route multiple skills, inherit benchmark contracts, detect near-duplicate skills, absorb behavioral eval results, audit skill safety/activation, or build a generator-of-generators.
---

# Ω-SKILLGEN-T∞ — Tristan Recursive Skill Foundry

Treat a Skill as a versioned behavioral program, not a prompt fragment.

## Canonical loop

`INTENT → MINE/SPECIFY → GENERATE → LINT → TRUST → EVAL → ATTACK → OAK → M-/M+ → MUTATE/REPAIR → REGRESSION → PROMOTION CANDIDATE`

For existing Tristan generators use the extended loop:

`GENERATOR RECORD → SKILLSPEC → BENCHMARK CONTRACTS → CVCD/SKILLGENOME → SKILL CANDIDATE → OAK/EVAL → BEHAVIORAL TELEMETRY → M+/M- → CAMPAIGN → PROMOTION LEDGER`

## Workflow

1. Identify the reusable workflow and success contract.
2. Prefer authorized execution traces or existing Generator Discovery records when they provide stronger provenance than free-form reconstruction.
3. Build or infer a SkillSpec.
4. If linked Generator Discovery benchmarks exist, inherit their expected contracts, negative controls, and OAK labels without upgrading synthetic templates into empirical evidence.
5. Run CVCD primitive extraction and SkillGenome similarity before proliferating a large family; reuse materially common primitives and review near-duplicate candidates.
6. Generate candidate skills outside this parent bundle.
7. Lint structure and activation metadata.
8. Run trust/OAK static review.
9. Require positive, negative, incomplete, and edge/adversarial eval coverage.
10. Preserve failures as M- and turn them into regression cases.
11. Compose only the smallest sufficient skill set and preserve the strictest overlapping invariant.
12. When actual behavioral/model eval results are supplied with usable provenance, summarize them, block behavioral promotion on must-pass failures, and split successes/failures into M+ and M- ledgers.
13. For self-improvement, generate multiple successor candidates and compare static evidence; never auto-promote the top heuristic score.
14. Advance promotion states one evidence gate at a time; preserve rollback provenance.

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

SkillGenome / behavioral telemetry:

- `python scripts/omega-skillgen-ops genome SPEC`
- `python scripts/omega-skillgen-ops dedup SPEC... --threshold X`
- `python scripts/omega-skillgen-ops telemetry RESULTS.json`
- `python scripts/omega-skillgen-ops memory RESULTS.json OUT`

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
- SkillGenome similarity is a deduplication review signal, not proof of semantic equivalence.
- `behavioral_eval_pass` summarizes supplied results only; provenance/authenticity of those results must be established separately.
- Any failed `must_pass` behavioral case blocks behavioral promotion.
- Prefer CVCD compression over near-duplicate skill proliferation.
- Generated child skills live outside the parent upload bundle.
- Preserve the strictest safety, approval, privacy, and epistemic invariant during composition.
- Recursive campaigns may rank candidates heuristically but `auto_promotion` remains false.
- Promotion states may not skip evidence gates; backward transitions require an explicit rollback reason.
- Preserve provenance from workflow traces or GeneratorRecord/BenchmarkRecord through generated SkillSpec, evals, mutations, telemetry, memories, and promotion decisions.

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

Use the parent foundry to regenerate or extend this ecology only through the same OAK, trust, regression, provenance, deduplication, telemetry, and promotion rules.
