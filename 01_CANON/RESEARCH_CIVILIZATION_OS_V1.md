# Ω-SELF-REGENERATING-RESEARCH-CIVILIZATION-OS-T∞Ω — Canon v1

## Status

Operational research architecture and prototype. It is not a scientific law, evidence of autonomous discovery, or evidence that simulated agents correspond to real researchers.

## Prime directive

For each question or residual, generate the **minimum finite research civilization** that can produce a useful independently verifiable capability, then distill verified results and remove unnecessary persistent structure.

`Question -> Residual -> Representation -> JIT Research Structure -> Attack -> Verify -> Distill -> Prune -> Regenerate`

## Primitive

The primitive is not University, Agent, Tristan, AIT, LLMT, or ALLT. The primitive is a **proof-carrying transformation capability**. Organizational forms are generated when they pay their complexity rent.

## Canonical objects

- `CompilationPolicy`: finite depth, unit budget, spawn margin, pruning threshold.
- `ResearchUnit`: generated capability-bearing unit; may be materialized or lazy.
- `CivilizationPlan`: deterministic plan for one question.
- `ClaimRecord`: claim + producer + falsifier + independent verifier + evidence + provenance.
- `ResearchSeed`: BOOK0-like minimum reconstruction seed.
- `ResearchCivilizationKernel`: planner/verifier/distiller. It performs no external side effects.

## Organizational search space

A plan may use: Virtual Tristan, AIT, LLMT, ALLT, research group, virtual university, simulation lab, scientific court, verifier, or no additional organization. The current v1 implementation materializes only what passes explicit finite gates; additional forms remain an extensible search space.

## Non-compensatory invariants

1. `Generator != Falsifier != Verifier` for promoted claims.
2. `Simulation != Observed reality`.
3. `Generated != Verified`.
4. Claim epistemic status must not exceed supporting evidence.
5. Every promoted claim requires provenance and at least one discriminating test.
6. Meta-depth is finite and bounded by a policy chosen before materialization.
7. A sub-civilization is created only when expected verified gain pays complexity rent + compute cost + margin.
8. Lazy candidates do not count as active capabilities until materialized.
9. Pruning must preserve the irreducible proposal/attack/verification separation.
10. Regeneration must reconstruct the required materialized capability graph from the seed without silently inventing missing parents or roles.
11. The kernel plans and verifies; it does not self-authorize external action.
12. `DO_NOTHING` / minimal structure remains a valid baseline.

## Minimum Scientific Civilization

The v1 irreducible research cell contains three independent roles:

1. Generator — proposes hypotheses/representations.
2. Falsifier — searches for counterexamples and hidden assumptions.
3. Verifier — audits evidence, replay, scope, and provenance.

AIT/LLMT/ALLT or institutions are added only when justified by the residual and explicit policy.

## JIT and lazy morphogenesis

Potential structure can be represented without execution. Materialization requires:

`ExpectedVerifiedGain - ComplexityRent - ComputeCost > MinimumSpawnMargin`

and `depth < max_depth`, parent materialization, and unit-budget availability.

This means conceptual possibility can be large while active compute remains bounded.

## Evidence semantics

The kernel reuses `omega_morphogenesis.EpistemicStatus`.

- Simulated evidence may support a simulated claim.
- A simulated claim is not marked as verified reality evidence.
- Verification begins at the observed rung in v1.
- Stronger statuses still require domain-appropriate evidence; the numeric ladder is a guard, not a universal theory of evidence.

## Apoptosis

Non-control units whose measured or estimated utility is below `minimum_unit_utility` may be pruned. Children cannot survive deletion of a required parent. Knowledge must be distilled before destructive lifecycle operations in production implementations.

## BOOK0 / regeneration

`ResearchSeed` stores only:

- question and residual identifiers;
- materialized unit blueprints;
- independently verified claim receipts with producer/falsifier/verifier identities, evidence status, provenance, and tests;
- finite compilation policy;
- source plan hash and version.

It intentionally excludes lazy unused candidates and simulation-only claims from durable verified knowledge.

## Metrics for v2+

- verified knowledge gain;
- independent verification coverage;
- hypothesis elimination rate;
- expected information gain;
- transfer across problems;
- regeneration closure;
- complexity rent;
- materialized/potential capability ratio;
- epistemic inflation count;
- common-mode verifier failure rate;
- future work eliminated.

## Falsifiers

The architecture is weakened or rejected if experiments show that:

- independent role separation does not reduce false promotion;
- JIT/lazy generation costs more than a fixed baseline without quality gain;
- BOOK0 regeneration fails to reconstruct required capability;
- meta-generation increases complexity without out-of-sample verified gain;
- pruning systematically removes capabilities later shown necessary;
- solver/representation diversity fails to improve discrimination relative to simpler baselines.

## OAK positioning

This repository may simulate or orchestrate virtual research organizations, but generated consensus is not truth, simulation is not experimentation, and agent count is not scientific quality. Real-world claims require appropriate external reality anchors.
