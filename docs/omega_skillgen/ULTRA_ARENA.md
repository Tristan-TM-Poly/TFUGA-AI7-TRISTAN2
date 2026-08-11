# Ω-SKILLGEN-T∞ — Ultra Evolutionary Skill Arena

This layer upgrades the foundry from single-candidate mutation into a controlled population laboratory.

## Core loop

`seed skills → fusion/fission → adaptive resource budget → SkillGenome novelty → hard OAK gates → Pareto fronts → diversity selection → behavioral evidence → M+/M- → promotion ledger`

## Why Pareto instead of one fitness number

A single scalar score can hide severe tradeoffs. A skill may be cheaper but less safe, more novel but less reliable, or highly accurate while over-triggering. The arena therefore uses non-dominated sorting across independent objectives such as behavioral pass rate, activation precision/recall, OAK score, novelty, reuse, risk, cost, and complexity.

No candidate may enter the Pareto arena if required structural/trust gates fail. High numeric scores cannot override a missing hard gate.

## Fusion

`crossover_specs(A, B)` preserves both parent lineages, unions declared invariants and tool policies, introduces an explicit conflict regression case, and requires the stricter safety/approval/privacy/epistemic rule whenever parents conflict.

## Fission

`fission_spec(S, i)` splits a long workflow into two traceable child candidates while retaining the full parent invariant set. Fission is useful when a monolithic skill over-triggers or mixes independent capabilities.

## Ω-SANS-PLAFOND-T budget

Population growth is controlled primarily by real resource budgets and novelty/backpressure rather than a fixed arbitrary candidate count. `max_candidates` is optional; JSON/resource capacity and novelty floors can stop campaigns naturally. This does not imply physically unbounded execution.

## Ecology audit

The ecology layer reports near-duplicate SkillGenome pairs, missing eval classes, shared invariants, compression debt, and lexical capability gaps. These are planning signals only; similarity is not semantic equivalence and lexical coverage is not proof that a capability works.

## OAK boundary

Pareto membership, novelty, fusion, or ecological coverage never imply `BEHAVIORAL_PASS`, scientific truth, product usefulness, or authorization to promote/merge. Promotion still requires the evidence-gated registry and real behavioral traces for behavioral claims.
