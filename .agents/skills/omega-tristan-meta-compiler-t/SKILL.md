---
name: omega-tristan-meta-compiler-t
description: Compress, generate, verify, automate, regenerate and prune Tristan-style theory/web/system architectures using a minimal proof-carrying kernel. Use for meta-generalization, meta-generation, meta-automation, BOOK0 regeneration, Theory-as-Code, capability morphogenesis, anti-meta simplification, or cross-domain compilation.
---

# Ω Tristan Meta-Compiler T

## Purpose

Turn a proliferating family of theories, generators, agents, worlds and institutions into the smallest reusable architecture that preserves verified capability.

## Mandatory invariants

- ClaimScope <= EvidenceScope.
- Generator != Judge.
- Generated != Verified.
- Simulation != Reality.
- Capability != Authority.
- MetaDepth <= VerifiedGain.
- PersistentStructure <= VerifiedNecessaryStructure.
- NO_ACTION and GO_MIN are always candidates.

## Input IR

Normalize work into TristanIR primitives:

`Claim, Evidence, Model, Capability, Actor, Resource, Experiment, World, Policy, Receipt, Residual`.

Unknown fields remain unknown.

## Workflow

1. OBSERVE current state and evidence.
2. RESIDUALIZE the unresolved question/capability gap.
3. REPRESENT using an explicit IR; tournament alternatives if useful.
4. GENERATE a bounded candidate set including GO_MIN and NO_ACTION.
5. COUNTERGENERATE the strongest baseline, countermodel and falsifier.
6. PROBE with the smallest discriminating test.
7. VERIFY using independent judge roles and hard gates.
8. GOVERN permissions/authority separately from capability.
9. TRANSFORM only the minimal verified delta.
10. RECEIPT every persistent transformation.
11. MEASURE against baseline, cost, risk and complexity.
12. DISTILL M+ / M- and unresolved residuals.
13. PRUNE/MERGE/DERIVE structures not carrying necessary capability.
14. REGENERATE from BOOK0 when useful.
15. META-VERIFY the generator/verifier/regenerator before promoting a new meta layer.

## Anti-meta rule

Before creating `META^(n+1)`, try: delete, parameterize, compose, merge, change representation, reuse an existing primitive. Create a new meta layer only if measured verified gain exceeds complexity, compute, risk and governance debt.

## Automation gradient

A0 manual; A1 suggest; A2 human-approved execution; A3 bounded sandbox autonomy; A4 zero-touch only inside an explicit verified safe envelope; A5 self-regenerating automation still subordinate to authority and independent verification.

## Output

Produce the minimum necessary combination of TristanIR objects, candidate transformations, baseline/countercandidate, OAK gate results, minimal experiment, universal receipt, M+/M- update, prune/merge/derive decision, BOOK0 delta, residuals and unresolved permissions.

Never present a generated architecture as proven optimal or a simulation as evidence from reality.

## Meta-skill civilization bridge

When the target is a skill ecology, do not create a second skill orchestrator. Reuse
`omega_skillgen_t` for SkillSpec generation/evals/trust/evolution and compile the
meta-level decision through `omega_tristan_meta.skill_civilization`.

Required counterfactuals:

```text
NO_ACTION
REUSE
COMPOSE
GENERATE_RESIDUAL
```

Select only an evidence-bearing verified sufficient plan. Generated residual skills stay
`CANDIDATE` with `auto_promote=false`.

For multi-skill plans, run ablation before crystallization. A removable skill becomes an
ablation candidate, never an automatic deletion.

Meta-improvement requires:

```text
Generator != Judge
independent evidence
VerifiedGain > ComplexityDebt + RiskDebt + MetaDebt
```

Crystallization requires verified sufficiency, evidence refs, tests and independent
judging. Emit only a candidate crystal and deterministic regeneration seed. A digest is
an identity/provenance aid, not proof of semantic equivalence.

Candidate BOOK0: `book0/BOOK0_META_SKILL_CIVILIZATION_R01.json`.

CLI smoke:

```bash
python -m omega_tristan_meta.cli skill-example
```
