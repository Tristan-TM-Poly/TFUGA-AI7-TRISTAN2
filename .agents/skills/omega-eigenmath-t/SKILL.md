---
name: omega-eigenmath-t
description: Compile mathematical research questions into typed ProblemGenomes, proof obligations, residuals, falsification attacks, proof-debt controls, proof/failure crystals, and regenerative seeds. Use for theorem or proof auditing, formal mathematical discovery workflows, Millennium benchmark work, proof-vs-numerical-evidence separation, generator/judge separation, or meta-improvement of mathematical research machinery.
---

# Ω-EIGENMATH-T∞ — Proof-Carrying Mathematical Discovery

Treat every new lemma, conjecture, derivation, or proof as `UNPROVEN` until the declared evidence gate is satisfied.

## Workflow

1. `SPECIFY`: bind the exact statement, definitions, assumptions, scope, and formal system.
2. `FORMALIZE`: create a `FormalizationReceipt`; translator and reviewer must be distinct identities.
3. `RESIDUALIZE`: decompose the frontier into explicit mathematical obligations with dependencies and uncertainty.
4. `GENERATE`: candidate lemmas, representations, and proof plans remain `UNPROVEN` by default.
5. `ATTACK`: run counterexample, assumption, circularity, scope, quantifier, and formalization-gap attacks.
6. `PROVE`: attach a proof artifact when formal status is requested; numerical evidence never substitutes for proof.
7. `VERIFY`: require independent replay for the highest internal status and keep formalization review separate from proof checking.
8. `NOVELTY`: judge truth, novelty, and importance separately; reproduced mathematics is not a new theorem.
9. `CRYSTALLIZE`: persist independently verified positive results as `ProofCrystal` and reusable failures as `FailureCrystal`.
10. `REGENERATE`: measure closure against declared crystals; never rename object replay as clean-room rediscovery.
11. `META-IMPROVE`: add a new meta-level only when frozen out-of-sample verified gain pays its added complexity, risk, and epistemic debt.
12. `STOP/COMPRESS`: when proof debt exceeds the configured ceiling, switch from generation to `VERIFY_ATTACK_COMPRESS`.

## OAK invariants

- `Generated != Proven`.
- `Formalized != FaithfullyFormalized`.
- `NumericalEvidence != Proof`.
- `NumericallySupported != Universal`.
- `Reproduced != Novel`.
- `Novel != Important`.
- `EquivalentOnTests != Equivalent`.
- `Generator != Judge != Falsifier` for material promotion decisions.
- `SelfImprovement != SelfApproval`.
- `MillenniumCandidate != MillenniumSolved`.
- `BenchmarkPASS != DiscoveryAbility`.
- `DigestEquality != SemanticEquivalence`.
- `Capability != Authority`.
- `LocalPASS != MathematicalCommunityAcceptance`.

## Millennium boundary

The six open Millennium problems are represented as `BOSS_LOCKED_UNPROVEN`. Never label one solved from internal generation, simulation, numerical exploration, benchmark success, a single formal artifact, or a single verifier. The R0 kernel may organize and attack candidate work, but external mathematical review and acceptance remain outside its authority.

Poincaré is a historical positive-control candidate for a later clean-room reconstruction benchmark; it must not be used as hidden solution leakage into held-out discovery tests.

## Meta boundary

Meta-generalization, meta-generation, meta-automation, meta-improvement, meta-crystallization, and meta-regeneration are candidate transformations, not automatic progress. A new meta-layer must use frozen tests, independent judging, explicit complexity/risk/debt accounting, and measured out-of-sample gain. If the current kernel can already express the capability, prefer reuse/compression over another layer.

## Repository commands

```bash
python -m unittest -v tests.test_omega_eigenmath_t
python -m omega_eigenmath_t
python -m json.tool schemas/eigenmath_proof_obligation.schema.json > /dev/null
```
