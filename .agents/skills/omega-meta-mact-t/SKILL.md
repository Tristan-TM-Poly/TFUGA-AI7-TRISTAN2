---
name: omega-meta-mact-t
description: Minimize irreducible action, compute, persistent memory, attention, complexity, risk and irreversibility for a verified task. Use for least-transformation planning, GO_MIN/NO_ACTION comparison, Pareto resource optimization, meta-stop decisions, or future-work annihilation.
---

# Ω Meta-MACT T

## Purpose

Compile a goal into the smallest verified sufficient transformation, not the smallest-looking plan.

## Mandatory invariants

- Generator != Judge.
- Generated != Verified.
- Simulation != Reality.
- Capability != Authority.
- Minimum != Brittle.
- NO_ACTION, WAIT and REUSE are candidates.
- Pareto compare before scalar ranking.
- No external action from the planning kernel.

## Workflow

1. Define current state, target contract and evidence scope.
2. Enumerate explicit candidate transformations.
3. Add `NO_ACTION`, `WAIT`, `REUSE`.
4. Attach the full MACT resource vector.
5. Attach evidence, authority and rollback.
6. Run hard gates before optimization.
7. Remove Pareto-dominated eligible candidates.
8. Rank remaining candidates with declared weights and future-work leverage.
9. Emit a MACT receipt.
10. Distill successful transformations into reusable invariants.
11. Apply meta-stop: do not optimize if expected savings do not exceed optimization cost/debt.

## Output

Return candidate set, hard-gate outcomes, Pareto frontier, selected or HOLD decision, residuals, receipt, and one falsifier for the claimed resource improvement.
