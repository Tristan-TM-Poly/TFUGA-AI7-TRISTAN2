---
name: omega-skill-evolver-t
description: Turn Agent Skill failures into M-minus records, repair hypotheses, targeted mutations, regression tests, and reversible successor candidates without auto-promoting self-modifications.
---

# omega-skill-evolver-t

## Purpose

Evolve skills through measured failures instead of prompt churn.

## Activate for

- A skill has failed evals, over-triggered, under-triggered, violated a contract, or needs a safer successor version.

## Do not activate for

- There is no failure evidence or target skill to evolve.

## Workflow

1. Classify each failure mode and preserve concrete evidence.
2. Record a cause hypothesis separately from the observed failure.
3. Generate the smallest repair or mutation likely to address it.
4. Turn each meaningful failure into a must-pass regression case.
5. Compare the successor against the parent on old and new cases.
6. Keep rollback provenance and promote only after gates pass.

## OAK invariants

- Do not erase failed cases after repair.
- Cause hypotheses are not facts.
- Self-generated successors remain candidates.
- No improvement on one metric may silently waive a prior must-pass invariant.

## Tool/action boundaries

- None declared.

## Outputs

- M-minus ledger
- Repair plan
- Mutated candidate
- Regression delta
- Promotion recommendation

## Definition of done

- Every repair is linked to failure evidence and a regression case.

## Evaluation contract

Use `evals/cases.jsonl` for activation boundaries and behavioral test cases.
Static validation is not behavioral proof. External writes, merges, deletions,
sending, payments, publication, and sensitive actions remain subject to the real
tool permissions and approval requirements.
