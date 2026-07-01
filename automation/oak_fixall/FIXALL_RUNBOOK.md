# Ω-AUTO²-OAK-FIXALL-T Runbook

This runbook defines the safe operating procedure for whole-ecosystem GitHub repair loops.

## Operating cycle

```text
Observe → Decide → Act → Verify → Learn
```

## 1. Observe

Collect the full state across accessible repositories, prioritizing repositories owned by `Tristan-TM-Poly`.

Required observations:

- open PRs;
- draft PRs;
- stale branches;
- queued/failing checks;
- absent workflows;
- missing docs/tests/benchmarks;
- duplicate blockers;
- newly merged work;
- scope mismatch between PR body and diff;
- external status context such as Vercel.

## 2. Decide

Assign exactly one decision per item:

- `MERGE_NOW`;
- `REPAIR_SAFE`;
- `WAIT_COOLDOWN`;
- `BLOCK_M_MINUS`;
- `HUMAN_APPROVAL_REQUIRED`.

When multiple decisions seem possible, choose the safest one.

Decision precedence:

```text
HUMAN_APPROVAL_REQUIRED
> BLOCK_M_MINUS
> WAIT_COOLDOWN
> REPAIR_SAFE
> MERGE_NOW
```

## 3. Act

Allowed actions are additive only:

- create docs;
- create schemas;
- create validators;
- create tests;
- create runbooks;
- create reports;
- create synthesis files;
- update PR bodies or comments with blocker summaries;
- add dependency installation when a workflow already requires that dependency;
- add bounded deterministic fixtures.

Forbidden actions:

- force-push;
- delete branches;
- weaken checks;
- mark drafts ready;
- bypass branch protections;
- hide red checks;
- perform external legal/financial/public/sensitive actions.

## 4. Verify

Before any merge, verify:

```text
open=true
merged=false
draft=false
mergeable=true
checks green or GitHub status clean
no required external red status
no sensitive risk
scope coherent
head SHA locked
```

Use `expected_head_sha` on merges when available.

## 5. Learn

Every loop must record:

- successful repair pattern in `M+`;
- blocker pattern in `M−`;
- anti-repetition rule;
- next safest slice.

## Split strategy for large PRs

Large branches should not be forced through. Split them conceptually into:

```text
safe_docs_slice
safe_schema_slice
safe_tests_slice
safe_validator_slice
safe_fixture_slice
risky_runtime_slice
experimental_slice
external_action_slice
```

Only small safe slices should become automatic PRs.

## HyperAtlas #25 pattern

Observed blocker class:

```text
PR title/body: 64^6
Diff includes: 64^8 subtree
CI: no-network validation red or unstable
External: Vercel may be red
```

Correct fix-all response:

```text
1. Preserve 64^8 as experimental/draft or synthesis artifact.
2. Extract bounded 64^6 deterministic generator.
3. Add no-network validator.
4. Merge only the coherent 64^6 slice when checks are green.
```

## Draft PR pattern

Draft PRs are not failed. They are human-controlled pending states.

```text
draft=true → WAIT_COOLDOWN
```

Do not mark ready automatically.

## Mergeable false pattern

```text
mergeable=false → BLOCK_M_MINUS or HUMAN_APPROVAL_REQUIRED
```

Do not force rebase or force-push.

## External status red pattern

If repository history treats an external status as meaningful:

```text
external_status=red → HUMAN_APPROVAL_REQUIRED
```

Do not bypass without explicit human approval.

## Output contract

Each loop should produce a compact report:

```yaml
merged:
  - repo:
    pr:
    merge_commit:
repaired:
  - repo:
    pr_or_branch:
    commit:
    repair_type:
blocked:
  - repo:
    item:
    blocker:
    anti_repetition:
waiting:
  - repo:
    item:
    reason:
learned:
  m_plus:
  m_minus:
```
