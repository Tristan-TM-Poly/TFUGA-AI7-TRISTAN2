# Zero-Manual PR Forge

`Zero-Manual PR Forge` is the PR automation policy for Tristan's GitHub work.

It upgrades `Build-To-Green` from a passive merge watcher into an autonomous-safe repair loop:

```text
blocked PR
  -> inspect blockers
  -> preserve content
  -> repair additively
  -> synthesize safely when conflicts exist
  -> wait for checks
  -> merge only when clean/green with expected SHA
```

## Core rule

```text
Nothing routine is sent back to Tristan manually.
```

The system must keep trying safe automated work instead of asking for human conflict resolution, missing test fixes, import repair, documentation repair, validator repair, or CI triage.

## Safe tactics

Allowed tactics are preservation-first and additive:

- `repo_root_import_bootstrap` — fix script/demo imports without weakening CI;
- `add_regression_test` — encode a failure as a test;
- `add_validator` — add schema/check validation;
- `add_guardrail` — add OAK safety constraints;
- `preserve_branch_version` — copy branch-only content into a named preserved artifact;
- `realign_canonical_path` — restore a conflicted canonical path after preservation;
- `synthesize_canon_artifact` — create a merged canon document that separates stable definitions, prototype notes, speculative ideas, OAK warnings, and M⁻;
- `update_machine_report` — write a repair report instead of a vague manual request;
- `rerun_or_wait_checks` — wait for GitHub's verdict instead of merging during pending checks;
- `merge_with_expected_sha` — merge only once clean/green and unchanged.

## Hard forbidden actions

The forge must never:

- force-push;
- delete branches;
- rewrite history;
- mark drafts ready automatically;
- weaken, skip, or remove checks to create green status;
- expose secrets;
- bypass branch protection;
- merge while checks are pending/failing/ambiguous;
- execute public, legal, financial, health, destructive, or human-impact actions without OAK gates.

## Drafts

Draft PRs can be enriched, tested, documented, and guarded, but they remain drafts until an explicit ready decision exists outside this module.

## M⁻ failure memory

Every blocker should create or preserve an M⁻ memory entry:

```text
repository / PR / failure class / concrete blocker / unsafe shortcut / autonomous next action / anti-repetition rule
```

This prevents repeated failures from being treated as isolated events.

## Merge invariant

```text
Green = non-draft + open + mergeable + conflict-free + passing checks or GitHub clean + expected head SHA.
```

Anything else is a repair target, not a merge target.
