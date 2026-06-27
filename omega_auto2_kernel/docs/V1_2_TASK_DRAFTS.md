# AUTO² Task Drafts — v1.2 seed

Status: local dry-run artifact generator.  
Issue: #86.

## Purpose

`auto2 task-draft` turns a task description into a local review draft containing:

- workflow ID and purpose;
- inferred steps;
- expected outputs;
- OAK score and status;
- blockers and warnings;
- human approval categories;
- M⁻ notes;
- suggested labels.

It does **not** create a live issue, send a message, publish content, spend money, change permissions, or disclose sensitive material.

## Commands

```bash
auto2 task-draft "prepare a local review packet"
auto2 task-draft "prepare a local review packet" --format json
auto2 task-draft "prepare a local review packet" --output reports/task_draft.md
```

## OAK boundary

The output is a local artifact only. A separate approved process must review and approve any external action.

## M⁻

- Do not treat generated draft text as approval.
- Do not bypass OAK blockers.
- Do not convert warnings into live tasks without review.
- Do not use task drafts to perform external actions automatically.

## Verification

```bash
python -m pytest tests/test_issue_draft.py
```
