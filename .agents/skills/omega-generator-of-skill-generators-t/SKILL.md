---
name: omega-generator-of-skill-generators-t
description: Generate domain-specific Agent Skill generators from reusable primitives, domain constraints, eval families, OAK policies, and M-minus patterns, creating generators-of-skills rather than manually enumerating every skill.
---

# omega-generator-of-skill-generators-t

## Purpose

Scale skill creation through domain generators while controlling duplication and regression debt.

## Activate for

- The user wants a whole domain or family of skills rather than a single skill.

## Do not activate for

- One narrowly scoped skill is sufficient.

## Workflow

1. Define the domain boundary and exclusions.
2. Extract reusable behavioral primitives and domain invariants.
3. Define generator inputs, outputs, activation tests, and trust gates.
4. Generate a domain-generator SkillSpec.
5. Use the domain generator to produce a small diverse seed family.
6. Catalog/deduplicate seeds and retain only materially distinct capabilities.
7. Evolve the generator itself only through regression-gated successor candidates.

## OAK invariants

- Optimize reusable primitives, not raw skill count.
- Generated generators remain candidates until evaluated.
- A domain generator cannot grant permissions unavailable to its generated skills.

## Tool/action boundaries

- None declared.

## Outputs

- Domain generator SkillSpec
- Seed skill family
- SkillGraph
- Dedup report
- Generator eval suite

## Definition of done

- The generator produces distinct, eval-covered seed skills with explicit domain boundaries.

## Evaluation contract

Use `evals/cases.jsonl` for activation boundaries and behavioral test cases.
Static validation is not behavioral proof. External writes, merges, deletions,
sending, payments, publication, and sensitive actions remain subject to the real
tool permissions and approval requirements.
