# M-CHATGPT-OAK v2

Negative memory for ChatGPT failures during Tristan GitHub workflows.

## Core law

When Tristan says `Go @GitHub`, the workflow is not complete at PR open, CI green, or mergeable. The default complete state is merged.

```text
implement -> tests -> PR -> CI -> fix if red -> merge if green -> post-merge summary
```

## Failure memory

### MCHATGPT001: stopped before merge

Failure: stopped at PR open or CI green instead of merging.

Anti-rule: if the PR is from our workflow, CI is green, and the PR is mergeable, merge automatically.

### MCHATGPT002: stale CI status

Failure: final summary used an old queued/running status.

Anti-rule: before a final GitHub summary, refresh the PR head sha and workflow conclusion.

### MCHATGPT003: repeated CI checks

Failure: checked the same workflow state too many times.

Anti-rule: at most two checks per head sha unless there is failure or ambiguity.

### MCHATGPT004: rich connector message blocked

Failure: merge message with rich/special content was blocked.

Anti-rule: use short ASCII-safe merge titles and messages.

### MCHATGPT005: large README patch blocked

Failure: long README update was blocked.

Anti-rule: split long docs into short docs/topic.md files and atomic commits.

### MCHATGPT006: exports/tests incomplete

Failure: new module added without complete public exports or tests.

Anti-rule: every public module needs exports and import/function tests.

### MCHATGPT007: early summary

Failure: summarized before the final workflow state.

Anti-rule: distinguish pushed, PR open, CI green, mergeable, and merged.

## State machine

```text
START
BRANCH_READY
FILES_CHANGED
TESTS_ADDED
PR_OPENED
CI_RUNNING
CI_FAILED -> FIXING -> CI_RUNNING
CI_GREEN
MERGEABLE
MERGED
POST_MERGE_SUMMARY
```

## Safe exceptions

Automatic merge should stop only for real blockers such as legal/IP uncertainty, dangerous security impact, destructive data change, missing permission, or failed CI.

## OAK mini-gate

Before a GitHub final answer, ask:

1. Did I do the requested action?
2. Did I verify the latest state?
3. Did I avoid unnecessary human validation?
4. Did I merge if green and mergeable?
5. Did I report only real blockers?
6. Did I summarize after the final state?

## Compression

```text
Go GitHub for Tristan means code, test, PR, CI, fix, merge, summarize.
```
