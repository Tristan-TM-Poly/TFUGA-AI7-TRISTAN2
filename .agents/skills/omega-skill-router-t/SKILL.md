---
name: omega-skill-router-t
description: Route a request across multiple Agent Skills using the smallest sufficient set while preserving the strictest safety, approval, privacy, and epistemic invariants across composed workflows.
---

# omega-skill-router-t

## Purpose

Compose multiple skills without over-triggering or weakening child contracts.

## Activate for

- Several installed or available skills overlap or must cooperate on one task.

## Do not activate for

- Exactly one skill clearly handles the whole request without composition.

## Workflow

1. Classify the request against each candidate skill activation boundary.
2. Reject irrelevant skills using negative-control logic.
3. Select the smallest sufficient skill set.
4. Order or parallelize child workflows based on dependencies.
5. Preserve the strictest overlapping invariant.
6. Expose conflicts and unresolved routing uncertainty.

## OAK invariants

- Never claim a child skill was invoked without product/tool evidence.
- Use the smallest sufficient set.
- Composition cannot weaken child approval or safety constraints.

## Tool/action boundaries

- None declared.

## Outputs

- Routing decision
- Selected skill set
- Dependency order
- Conflict/residual report

## Definition of done

- The route is explicit, minimal, and preserves child constraints.

## Evaluation contract

Use `evals/cases.jsonl` for activation boundaries and behavioral test cases.
Static validation is not behavioral proof. External writes, merges, deletions,
sending, payments, publication, and sensitive actions remain subject to the real
tool permissions and approval requirements.
