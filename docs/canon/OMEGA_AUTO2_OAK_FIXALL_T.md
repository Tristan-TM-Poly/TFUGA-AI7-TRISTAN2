# Ω-AUTO²-OAK-FIXALL-T — GitHub Fix-All Orchestrator

Status: OAK-safe scaffold
Scope: GitHub repositories accessible to Tristan-TM-Poly, prioritizing owned repositories
Mode: observe, classify, repair additively, verify, merge only when clean, learn

## Purpose

Ω-AUTO²-OAK-FIXALL-T is the system that prevents repeated manual PR-by-PR debugging loops. It converts the whole GitHub ecosystem into a single OAK action graph:

```text
Repos → ObserveAll → BlockerGraph → SplitEngine → RepairBatch → VerifyMatrix → MergeQueue → M+/M−
```

The goal is not to force all work through. The goal is to extract safe micro-nuclei from noisy branches, repair repeatable blockers, and preserve risky or ambiguous material without destructive actions.

## Non-negotiable OAK boundaries

The system must not:

- force-push;
- delete branches;
- weaken required checks;
- expose secrets;
- bypass branch protections;
- mark drafts ready;
- perform legal, financial, public, sensitive, or external human-impacting actions;
- merge when draft, non-mergeable, checks are red/queued/absent, or scope is incoherent.

The system may only act on non-destructive additive fixes:

- docs;
- runbooks;
- tests;
- schemas;
- validators;
- reports;
- registry updates;
- conflict-preserving synthesis files;
- bounded deterministic fixtures;
- no-network test hardening;
- CI dependency installation when tests already require it.

## Canonical decisions

```text
MERGE_NOW
REPAIR_SAFE
WAIT_COOLDOWN
BLOCK_M_MINUS
HUMAN_APPROVAL_REQUIRED
```

### MERGE_NOW

Allowed only when every condition is true:

```text
open=true
merged=false
draft=false
mergeable=true
checks=green_or_clean
external_status=green_or_absent_but_not_required
risk=low
scope=coherent
diff=additive_or_safe
secrets=none
```

### REPAIR_SAFE

Use for deterministic additive fixes, such as:

- install `pytest` before running pytest;
- set `PYTHONPATH=src` when tests import local packages;
- add no-network smoke tests;
- add strict schema validation;
- add missing README/runbook;
- resync generated indexes;
- bound combinatorial generators;
- add conflict-preserving synthesis reports.

### WAIT_COOLDOWN

Use when the item is safe but not actionable yet:

- draft PR;
- checks queued/in progress;
- mergeability pending;
- freshly pushed repair commit;
- human-owned branch status intentionally paused.

### BLOCK_M_MINUS

Use when a repeated blocker has been observed and should not be retried blindly:

- CI red;
- mergeable=false;
- scope mismatch;
- Vercel red when treated as required by the repository context;
- hidden large subtree not described by PR title/body;
- absent workflows on a commit that needs verification.

### HUMAN_APPROVAL_REQUIRED

Use when the item is too broad or sensitive for automatic action:

- large orchestration PR;
- scheduled workflows;
- Drive/Gmail/Calendar/external connectors;
- public deployment;
- IP/legal/financial implications;
- ambiguity that cannot be resolved by additive files only.

## Core insight from current blocker history

Small additive PRs merge cleanly when they have green checks and coherent scope. Large branches often contain valuable material but should be decomposed instead of forced.

The system must prefer:

```text
extract safe slice → create small PR → verify → merge
```

over:

```text
repair giant branch forever → hope it becomes clean
```

## SplitEngine rule

Any large or inconsistent PR is split conceptually into slices:

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

Only safe slices can become automatic PRs. Risky slices remain draft or require human approval.

## Example: HyperAtlas blocker pattern

If a PR title/body says `64^6` but the diff includes a `64^8` subtree, the system must not silently merge. It should create or request a synthesis split:

```text
HyperAtlas Safe Extraction: 64^6 bounded generator + no-network validator
HyperAtlas Experimental Archive: 64^8 subtree preserved as draft/research
```

## M+ learned patterns

- Small additive PRs with visible green checks merge cleanly.
- Dedicated narrow CI for new reports reduces false-green ambiguity.
- Installing test dependencies explicitly prevents repeated `pytest: command not found` failures.
- Bounded deterministic generators prevent tensor explosion in CI.
- No-network validation is the correct default for repository automation.

## M− anti-repetition rules

- Never merge `draft=true`.
- Never merge `mergeable=false`.
- Never treat absent workflows as green.
- Never retry a red CI loop without adding a diagnostic or repair.
- Never merge a scope mismatch such as `64^6` PRs containing hidden `64^8` work.
- Never bypass Vercel or external statuses without explicit human approval.
- Never convert a broad branch into production by accident.

## MVP implementation plan

1. Add `fixall_manifest.yaml`.
2. Add `fixall_blocker_registry.yaml`.
3. Add `fixall_decision_schema.json`.
4. Add `FIXALL_RUNBOOK.md`.
5. Add dry-run only scripts later.
6. Add CI only after the schema and examples stabilize.

## OAK status

This document is a canonical scaffold and not an autonomous execution grant. Actual GitHub actions remain bounded by explicit OAK checks and repository protections.
