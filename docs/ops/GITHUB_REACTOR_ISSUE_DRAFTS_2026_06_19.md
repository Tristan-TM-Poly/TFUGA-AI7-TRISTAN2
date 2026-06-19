# GitHub Reactor Issue Drafts — 2026-06-19

Status: OAK-safe action proposal layer  
Root PR: #36

## 1. Purpose

The issue draft generator converts ranked Bayes-Tristan actions into reviewable issue drafts.

It does not open issues. It only writes artifacts.

## 2. Inputs

```text
reports/github-autonomous-reactor/bayes_tristan_action_scores.json
```

## 3. Outputs

```text
reports/github-autonomous-reactor/issue_drafts.json
reports/github-autonomous-reactor/ISSUE_DRAFTS.md
reports/github-autonomous-reactor/issue_draft_generator.log
reports/github-autonomous-reactor/issue_draft_generator_status.txt
```

## 4. Draft fields

Each draft carries:

```text
rank
repository
title
labels
body
source_score
allowed_mode = draft_only
```

## 5. OAK boundary

```text
Bayes-Tristan score -> issue draft -> human review -> explicit issue creation
```

No automated GitHub issue creation happens in this PR.

## 6. Why this matters

The Reactor now has a safe action bridge:

```text
ranked decision -> reviewable task packet
```

This is stronger than a report and safer than autonomous issue creation.

## 7. Canon rule

```text
Never convert a score directly into repository mutation.
Always convert score into a reviewable artifact first.
```
