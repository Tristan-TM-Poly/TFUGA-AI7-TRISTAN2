---
name: omega-workflow-miner-t
description: Mine authorized repeated workflows into evidence-backed Agent Skill candidates while separating recurrence from correctness and preserving source provenance.
---

# omega-workflow-miner-t

## Purpose

Discover which repeated workflows deserve crystallization as skills.

## Activate for

- The user asks to turn repeated work, traces, routines, or successful workflows into reusable skills.

## Do not activate for

- No authorized workflow evidence is available and the request is only a one-off task.

## Workflow

1. Collect only authorized workflow traces or explicit workflow descriptions.
2. Normalize steps and group equivalent workflows.
3. Measure recurrence, success evidence, and stable step candidates.
4. Separate common steps from optional/context-dependent steps.
5. Generate SkillSpec candidates with provenance and uncertainty.
6. Require negative/incomplete/edge activation tests before promotion.

## OAK invariants

- Frequency is not correctness.
- Do not mine private or unseen traces.
- A mined skill remains a candidate until evaluated.
- Preserve provenance from candidate primitives back to trace classes.

## Tool/action boundaries

- None declared.

## Outputs

- Mined workflow candidates
- Candidate invariant steps
- SkillSpec proposals
- Coverage gaps

## Definition of done

- Every candidate has provenance, activation boundaries, and at least one falsifying/negative case.

## Evaluation contract

Use `evals/cases.jsonl` for activation boundaries and behavioral test cases.
Static validation is not behavioral proof. External writes, merges, deletions,
sending, payments, publication, and sensitive actions remain subject to the real
tool permissions and approval requirements.
