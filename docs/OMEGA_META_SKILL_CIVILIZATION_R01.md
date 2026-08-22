# Ω-META-SKILL-CIVILIZATION-T∞Ω — R0.1

## Mission

Close the missing executable bridge between the repository's existing `Ω-SKILLGEN-T∞`
and `Ω Tristan Meta-Compiler / Meta-Morphogenesis` without creating a parallel
orchestrator.

The R0.1 loop is:

```text
INTENT
→ RESIDUALIZE
→ SEARCH EXISTING SKILLS
→ COUNTERFACTUALIZE
   {NO_ACTION, REUSE, COMPOSE, GENERATE_RESIDUAL}
→ SELECT MINIMUM VERIFIED SUFFICIENT PLAN
→ ABLATE
→ META-VERIFY
→ CRYSTALLIZE
→ REGENERATE
```

The unit of progress is verified capability, not skill count.

## Reuse-first architecture

This layer deliberately reuses:

- `omega_skillgen_t` for SkillSpec generation, mutation, behavioral evals, trust,
  lineage, deduplication and promotion gates;
- `omega_tristan_meta` for meta-governance, proof-carrying receipts, regeneration
  and the Generator != Judge constitution;
- `omega_morphogenesis` as the canonical authority/epistemic kernel underneath the
  Tristan meta adapter.

It does **not** duplicate those engines.

## R0.1 executable surface

`omega_tristan_meta.skill_civilization` adds:

- `SkillGenome` — compact capability/cost/risk/evidence representation;
- `SkillPlan` — typed counterfactual skill program;
- `meta_generalize()` — evidence-bearing cross-skill invariant candidates;
- `compile_counterfactual_plans()` — bounded `NO_ACTION / REUSE / COMPOSE /
  GENERATE_RESIDUAL` worlds;
- `select_minimum_sufficient_plan()` — verified minimum sufficient plan selector;
- `generate_residual_skill_candidates()` — candidate-only missing-capability
  generation contracts;
- `ablation_report()` — identify removable skills without authorizing deletion;
- `evaluate_meta_improvement()` — independent-judge + meta-complexity-rent gate;
- `meta_depth_decision()` — stop META^(n+1) when verified gain does not repay added
  complexity, compute, risk and meta debt;
- `crystallize_skill_plan()` — candidate crystal gate;
- `regeneration_seed()` — deterministic content-addressed seed;
- `regeneration_closure()` — explicit capability closure metric.

The CLI smoke path is:

```bash
python -m omega_tristan_meta.cli skill-example
```

## Meta-generalization

R0.1 only extracts capability intersections from skills that are both:

1. declared verified; and
2. linked to at least one evidence reference.

The output status is `CANDIDATE`, never `UNIVERSAL`.

```text
cross-skill invariant candidate != universal law
```

## Meta-generation

Missing capabilities produce `GENERATE_RESIDUAL` candidates only.

Every generated skill candidate remains:

```text
status = CANDIDATE
auto_promote = false
```

and requires:

- SkillSpec;
- trust review;
- positive / negative / incomplete / adversarial evals;
- behavioral evidence;
- independent judge.

Generation never creates promotion authority.

## Meta-automation

R0.1 automates **planning and verification bookkeeping**, not unrestricted external
execution.

It may automatically:

- enumerate bounded counterfactual skill programs;
- compute residuals;
- select a verified minimum sufficient plan;
- compute ablation candidates;
- calculate meta-depth decisions;
- build deterministic crystal/seed digests.

It does not automatically:

- write to external systems;
- merge PRs;
- delete skills;
- widen permissions;
- promote generated skills;
- claim behavioral validity from static metadata.

## Meta-regeneration

A promoted candidate crystal is represented by the minimum deterministic payload:

```text
capabilities
+ source skill lineage
+ evidence references
+ kernel operations
+ digest
```

A `RegenerationSeed` is content-addressed from that crystal.

The explicit closure metric is:

```text
RegenerationClosure =
|RequiredCapabilities ∩ RegeneratedCapabilities|
/ |RequiredCapabilities|
```

`1.0` on a bounded fixture does not prove universal regenerability or justify deletion
of historical artifacts.

## Meta-improvement

A meta-improvement is accepted only if all of the following hold:

```text
Generator != Judge
independent_evidence = true
VerifiedGain > ComplexityDebt + RiskDebt + MetaDebt
```

The receipt always keeps:

```text
auto_promoted = false
```

The system may therefore conclude that an additional meta layer is not worth keeping.

## Meta-crystallization

Crystallization requires:

- a verified sufficient plan;
- evidence references;
- independent evidence;
- passing tests;
- separate generator and judge roles.

The result is `CANDIDATE_CRYSTAL`, not eternal truth.

A crystal can be re-opened, invalidated, superseded or regenerated.

## Ablation / apoptosis

For every selected multi-skill plan, R0.1 removes each skill in simulation and checks
whether required capability coverage survives.

A skill that is removable becomes an **ablation candidate** only.

```text
ablation candidate != deletion authority
```

`automatic_deletion_authorized` is permanently `false` in this layer.

## Counterfactual worlds

Every bounded planning court includes at least:

```text
W0 = NO_ACTION
W1 = REUSE
W2 = COMPOSE
W3 = GENERATE_RESIDUAL
```

This makes "do nothing", reuse and composition first-class competitors to new skill
generation.

## Candidate BOOK0

`book0/BOOK0_META_SKILL_CIVILIZATION_R01.json` stores the bounded regenerative kernel:

```text
INTENT
RESIDUALIZE
SEARCH
COUNTERFACTUALIZE
REUSE
COMPOSE
GENERATE_RESIDUAL
VERIFY
ABLATE
CRYSTALLIZE
REGENERATE
```

Its presence is not a minimality proof. Future R0.x work should run true ablation and
reconstruction courts against frozen capability probes.

## OAK constitution

```text
Generated != Verified
Generator != Judge
SelfModification != SelfApproval
ToolAvailable != ToolNecessary
Capability != Authority
MoreSkills != MoreCapability
MoreMeta != Better
PersistentStructure <= VerifiedNecessaryStructure
```

Additional non-claims:

```text
candidate BOOK0 != minimality proof
deterministic digest != semantic equivalence
software PASS != scientific truth
verified metadata != behavioral capability
ablation survival != safe destructive deletion
regeneration fixture != universal regeneration
```

## R0.1 tests

`tests/test_meta_skill_civilization.py` covers:

1. candidate-only meta-generalization;
2. all four counterfactual modes;
3. minimum verified sufficient plan selection;
4. rejection of unverified apparent sufficiency;
5. residual generation with no auto-promotion;
6. ablation without deletion authority;
7. Generator != Judge and complexity-rent improvement gate;
8. meta-depth STOP;
9. deterministic crystallization and regeneration seed;
10. fail-closed crystallization without independent evidence;
11. explicit regeneration closure.

## Next falsification frontier

R0.2 should not primarily add more abstractions. It should attack R0.1 with:

1. real SkillSpec adapters instead of compact hand-built `SkillGenome` fixtures;
2. cross-domain capability probe sets;
3. representation tournament:
   `SkillGenome` vs direct SkillSpec vs minimum dict vs `NO_ABSTRACTION`;
4. randomized and adversarial ablation orders;
5. behavioral-eval receipts from `omega_skillgen_t`;
6. false-sufficiency tests where lexical capability overlap hides incompatible
   semantics;
7. option-value / maintenance-debt measurements;
8. actual reconstruction from BOOK0 into a clean sandbox;
9. negative cases where `NO_ACTION` or a simpler direct workflow wins;
10. independent review before any merge or destructive pruning.

## Status

Engineering R0.1 / candidate crystal.

It is a bounded proof-carrying planning and regeneration layer. It is not evidence of
AGI, universal optimality, scientific truth, safe autonomous authority, or permission
for destructive self-modification.
