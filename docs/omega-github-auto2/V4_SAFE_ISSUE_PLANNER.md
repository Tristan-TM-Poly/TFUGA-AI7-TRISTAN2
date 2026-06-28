# Omega AUTO2 v4 Safe Issue Planner

This v4 layer adds a manual, auditable P0 issue planner on top of the merged v3 reactor.

## Purpose

Turn selected Top1024 P0 cards into GitHub issues in a controlled way.

## Default behavior

The planner is dry-run by default. It writes an audit JSON and prints the planned issue batch.

Real issue creation requires:

```bash
--execute
```

## OAK safety rules

- Manual workflow dispatch only.
- No scheduled autonomous drip.
- No hidden or stealth behavior.
- Batch limit must be between 1 and 8.
- Existing open issues are skipped.
- Labels are limited to existing safe labels by default.
- Audit JSON is always written.

## Commands

Dry-run:

```bash
python scripts/omega_auto2_issue_planner_v4.py \
  --manifest artifacts/omega_github_auto2/top1024_manifest.json \
  --limit 4
```

Execute:

```bash
python scripts/omega_auto2_issue_planner_v4.py \
  --manifest artifacts/omega_github_auto2/top1024_manifest.json \
  --limit 4 \
  --control-issue 112 \
  --execute
```

## Workflow

The workflow is:

```text
.github/workflows/omega-auto2-issue-planner-v4.yml
```

It first regenerates AUTO2 artifacts from the v3 factory, then runs the v4 planner in dry-run or execute mode depending on the manual input.
