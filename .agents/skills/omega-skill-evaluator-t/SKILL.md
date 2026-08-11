---
name: omega-skill-evaluator-t
description: Evaluate Agent Skill candidates for activation precision, negative controls, incomplete inputs, edge cases, output contracts, OAK invariants, and runtime evidence boundaries.
---

# omega-skill-evaluator-t

## Purpose

Prevent structurally valid skills from being mistaken for behaviorally validated skills.

## Activate for

- The user asks to test, score, audit, benchmark, or validate a skill.

## Do not activate for

- The user only wants to draft a one-off response.

## Workflow

1. Lint the skill package and manifest.
2. Check positive, negative, incomplete, and edge/adversarial coverage.
3. Inspect tool/action and approval boundaries.
4. Run or request runtime/model evals when behavioral claims matter.
5. Compare must-pass regressions with previous versions.
6. Emit a promotion state and unresolved evidence gaps.

## OAK invariants

- STATIC_PASS is not BEHAVIORAL_PASS.
- Never infer runtime invocation from file structure alone.
- Promotion requires declared evidence for each claimed quality dimension.

## Tool/action boundaries

- None declared.

## Outputs

- Evaluation matrix
- Promotion state
- Regression failures
- Evidence gaps

## Definition of done

- Every claimed PASS state names the evidence that supports it.

## Evaluation contract

Use `evals/cases.jsonl` for activation boundaries and behavioral test cases.
Static validation is not behavioral proof. External writes, merges, deletions,
sending, payments, publication, and sensitive actions remain subject to the real
tool permissions and approval requirements.
