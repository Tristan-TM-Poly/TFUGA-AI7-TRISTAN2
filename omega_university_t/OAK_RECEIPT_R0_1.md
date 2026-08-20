# OAK Receipt — Ω University R0.1

## Claim scope

R0.1 claims only that a finite capability prerequisite graph can be compiled into a deterministic missing-capability order with explicit fail-closed behavior and planning-only authority boundaries.

It does **not** claim:

- educational superiority;
- causal learning effectiveness;
- accreditation or credential validity;
- safe inference of a person's cognition;
- research-frontier correctness;
- institutional governance completeness;
- autonomous execution authority.

## Software court

Focused tests cover:

1. prerequisite ordering;
2. verified-capability cut sets;
3. deterministic target deduplication;
4. unknown-target rejection;
5. unresolved-prerequisite rejection;
6. explicit verified external prerequisites;
7. reachable-cycle rejection;
8. deterministic receipts and hard-false authority/credential/proof fields;
9. empty-target rejection.

CI command:

```bash
python -m unittest discover -s omega_university_t/tests -p 'test_*.py' -v
```

## Epistemic type

```text
architecture: CONJECTURED / SPECIFIED
compiler behavior: TESTABLE SOFTWARE CLAIM
educational effectiveness: UNMEASURED
credential authority: NONE
external action authority: NONE
```

## M- seeds

- `M-UNIV-COURSE-EQUALS-CAPABILITY`: completing content is not proof of capability.
- `M-UNIV-PLAN-EQUALS-LEARNING`: a dependency plan is not a measured learning intervention.
- `M-UNIV-TESTS-EQUALS-PEDAGOGY-PROOF`: repository tests cannot prove educational outcomes.
- `M-UNIV-GLOBAL-HUMAN-SCORE`: never collapse a person's worth into a single global score.
- `M-UNIV-SELF-CERTIFICATION`: generator and final verifier must remain separable for consequential claims.

## Required next evidence

Before promoting any claim about learning effectiveness, run a bounded comparison against a declared baseline measuring at least retention, transfer, time/cost, uncertainty, and attrition. Preserve `NONE` / no-change as a baseline and perform ablations on prerequisite assumptions.

## Promotion gate

```text
ExactHeadPASS required
LocalPASS != GlobalPASS
Generated != Verified
CurriculumPlan != Learning
VerifiedCapability != Credential
```
