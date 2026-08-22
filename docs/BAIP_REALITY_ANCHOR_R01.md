# BAIP Reality Anchor R0.1

Status: **PRE-MEETING DRAFT / HOLD**

This artifact is deliberately smaller than the prior BAIP material. It does not ask BAIP to evaluate the whole Tristan corpus. It asks whether one bounded educational experiment is worth specifying.

## Core question

Does AI merely improve task performance while available, or does an AI-assisted intervention leave a capability that remains when AI is withdrawn?

Core distinction:

`SystemPerformedTask != BeneficiaryAcquiredCapability`

## Candidate comparison

1. Human only.
2. Human + checklist.
3. Human + AI.
4. Human + AI + minimal verification.

The primary outcome should be an independently scored transfer/understanding task completed **without AI after withdrawal**, not immediate assisted performance.

## What is already fixed conceptually

- The current teaching/practice can remain a valid baseline.
- AI benefit is not presumed.
- Verification benefit is not presumed.
- Null and negative results are valid outcomes.
- Acceptance/adoption rate is not a success criterion.
- Participants must have real opt-out and contestation routes before execution.
- Any material protocol or system change requires reconsultation.
- Software tests do not count as evidence of pedagogical efficacy.

## Decisions that must come from the real context

The candidate remains `HOLD` until the meeting/context determines:

- the authentic engineering learning task;
- the real student/learner population and instructor/course partner;
- whether four conditions are feasible or a smaller design is more appropriate;
- the primary transfer observable and scoring rubric;
- the delayed replay window;
- the independent evaluator role;
- applicable consent, ethics and institutional governance;
- opt-out, feedback/contestation and stop/rollback procedures;
- dependency measure after AI withdrawal;
- whether the pilot is useful enough to justify the burden at all.

## Five meeting questions

1. **Need:** What concrete pedagogical problem is worth measuring here?
2. **Task:** What authentic engineering task could be repeated/scored without creating artificial coursework?
3. **Partner:** Which teacher/course/context could legitimately own the pedagogical side?
4. **Governance:** What approvals, consent or ethics route would apply before any real participant is involved?
5. **Kill criterion:** What result or practical constraint should make us stop rather than expand the pilot?

## Decision states

- `HOLD` — missing real information or governance.
- `REVISE` — question is useful but current design is wrong or too burdensome.
- `NO_ACTION` — no sufficiently useful/ethical/feasible pilot exists.
- `PILOT_ELIGIBLE` — protocol is complete enough to consider formal preregistration, subject to real authority.

`PILOT_ELIGIBLE != AUTHORIZED`.

## Immediate post-meeting output

Do not send a large follow-up package by default. Convert the meeting into one short decision receipt:

`Need -> Candidate task -> Partner -> Governance path -> Missing evidence -> Next decision`

Only then update `pilots/quebec/baip_learnverify_candidate.draft.json`. If `TBD` fields remain, the preregistration court must continue to return `HOLD`.
