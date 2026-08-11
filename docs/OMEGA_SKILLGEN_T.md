# Ω-SKILLGEN-T∞ v0.2 — Tristan Recursive Skill Foundry

## Thesis

A reusable workflow becomes a Skill only after its activation boundary, procedural invariants, tool/permission boundaries, evaluation cases, provenance, and failure memory are explicit.

## Canonical loop

`INTENT → MINE/SPECIFY → GENERATE → LINT → TRUST → EVAL → ATTACK → OAK → M- → MUTATE/REPAIR → REGRESSION → PROMOTION CANDIDATE`

## Implemented layers

1. **WorkflowMiner** — extracts recurring candidate workflows from authorized traces.
2. **SkillCompiler** — compiles `SkillSpec → SKILL.md + evals + provenance`.
3. **TrustGate** — heuristic scan for approval bypass, credential language, destructive actions, exfiltration language, and epistemic overclaim.
4. **EvalGate** — requires positive, negative, incomplete, and edge/adversarial coverage.
5. **SkillComposer** — routes the smallest sufficient child set and preserves the strictest overlapping invariant.
6. **DomainGenerator** — produces specialized generator-of-skills specifications.
7. **MutationEngine** — activation-precision, OAK-hardening, and eval-hardening mutations plus structural diff.
8. **SkillCatalog/HGFM** — indexes manifests, signatures, duplicate groups, and the L0-L5 SkillGraph.
9. **M- Evolution** — converts failed evals into repair plans and must-pass regression obligations.

## OAK states

`DRAFT → STATIC_PASS → EVAL_READY → TRUST_REVIEWED → BEHAVIORAL_PASS → PROMOTE_CANDIDATE → PROMOTED`

These states are intentionally non-equivalent. In particular, `STATIC_PASS != BEHAVIORAL_PASS`.

## Recursive architecture

`workflow → skill → family → router/composition → domain generator → generator-of-generators`

The objective is not to maximize raw skill count. It is to maximize activation precision × usefulness × evidence × composability × reuse while minimizing duplication × unsafe authority assumptions × brittle workflows × regression debt.

## OpenAI product boundary

Skills describe reusable workflow guidance and can include instructions, examples, and code. Tool/app permissions remain separate capabilities. Imported skills should be reviewed and treated as untrusted until their instructions and resources are understood. The foundry therefore never treats a generated Skill as granting permissions or as automatically installed in ChatGPT/Codex.

## Fractal HGFM representation

- L0 — trigger, step, guard, resource, eval, tool-boundary atom.
- L1 — Skill.
- L2 — Skill family.
- L3 — router/composition.
- L4 — domain generator.
- L5 — generator-of-generators.

A node at any level may expand into the hypergraph below it while still participating as one node in the level above.

## CVCD rule

Repeated workflows are compressed into reusable primitives only after evidence. Frequency is not correctness; exact duplicates are debt; similar workflows should share primitives rather than multiply blindly.

## Promotion rule

A candidate advances only when deterministic structure/eval checks pass, trust findings are reviewed, must-pass regressions remain passing, provenance and rollback exist, and any claimed behavioral quality is backed by actual model/runtime evaluation.
