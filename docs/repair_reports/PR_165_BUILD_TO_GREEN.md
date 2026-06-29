# PR #165 Build-To-Green repair report

PR: `#165 — Ω-ACTION-EXT-T MVP: OAK-safe external action kernel`

## Decision

`manual_required`

## Current state

- PR is open but still marked `draft`.
- Branch head inspected: `dff4e4eeeb985cf6dfd8301b53a503165d9fa6c6`.
- Workflow status observed for this head: `omega-action-ext-t-tests` completed with `success`.
- GitHub still reports `mergeable=false`, so the PR must not be merged automatically.

## Why not merge automatically

This PR touches an external-action kernel: even though the current MVP is dry-run-first, its future surface includes email, calendar, GitHub, Drive, payments, publication, permissions, reputation, IP and legal-sensitive actions. The PR body intentionally keeps it in draft until the OAK review is complete.

## Safe path to green

1. Keep the PR as draft until human OAK review confirms the public-safe scope.
2. Confirm there are no live connectors, secrets, tokens, write actions, payment actions, public-post actions, or permission changes in the MVP.
3. Confirm every action path defaults to dry-run, draft, approval, expert review, or block.
4. Add/verify tests for:
   - destructive action without rollback => block;
   - email/outreach without approval => draft only;
   - public disclosure/IP-sensitive action => approval/review;
   - critical risk => expert/human gate;
   - low-risk reversible action => allowed only inside declared sandbox.
5. Re-check GitHub mergeability after updating against `main`.
6. Merge only after the PR is no longer draft, is clean/mergeable, and all required checks are green.

## Forbidden actions

- Do not mark ready automatically.
- Do not bypass draft status.
- Do not expose secrets or add live credentials.
- Do not add real-world actuators without dry-run and explicit approval gates.
- Do not merge while `draft=true` or `mergeable=false`.

## OAK invariant

```text
External action autonomy requires proof, approval boundaries, rollback, and least privilege before execution.
```
