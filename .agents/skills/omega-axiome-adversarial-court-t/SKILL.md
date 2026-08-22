---
name: omega-axiome-adversarial-court-t
description: Stress-test an AxiomGenome or ClaimPassport with counterclaims, negations, scope restrictions, boundary hunts, stronger baselines, mutation tests, and discriminating predictions. Use when a theory should be attacked rather than merely expanded, when competing hypotheses need separation, or when the user asks what could falsify or weaken an axiom.
---

# Ω‑AXIOME‑ADVERSARIAL‑COURT‑T∞

Maximize discriminating information, not rhetorical victory.

## Attack grammar

Given candidate `A`, generate only bounded research candidates such as:

- `NEGATE(A)`;
- `NARROW_SCOPE(A)`;
- `BOUNDARY_HUNT(A)`;
- strongest known baseline;
- plausible alternative mechanism;
- assumption deletion;
- quantifier weakening/strengthening where semantically meaningful;
- prediction collisions under matched conditions.

Every generated variant must retain lineage to its parent.

## Court loop

`CLAIM → MUTATE → FIND DISAGREEMENT → DEFINE OBSERVABLE → FIND MINIMAL DISCRIMINATING PROBE → OAK → KEEP/BOUND/REFUTE/HOLD`

Prefer the smallest probe that can separate serious alternatives at acceptable cost and risk. A probe candidate is a research plan, not automatic permission to execute it.

## Required adversarial checks

1. strongest baseline before novelty claims;
2. explicit counterhypothesis rather than straw-man opposition;
3. scope/boundary attacks;
4. counterexample search;
5. mutation sensitivity;
6. alternative explanations;
7. generator/falsifier/judge separation for material promotions;
8. preserve the strongest surviving *bounded* claim rather than forcing binary victory.

## OAK invariants

- `Counterclaim != Evidence`.
- `HeuristicScore != TruthScore`.
- `AbsenceOfCounterexample != Proof`.
- `DiscriminatingPrediction != AuthorizedExperiment`.
- `Generator != Falsifier != Judge` when practical and material to the decision.
- Do not reward mutation count; reward measured information gain and error detection.
- A mutation that changes the meaning must be labeled as a new candidate, not a faithful restatement.
- If alternatives remain observationally equivalent under available probes, return `NON_IDENTIFIABLE` or `HOLD` instead of inventing a winner.
