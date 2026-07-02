# Manifest Spec

A manifest is a review packet for a proposed external operation. It does not execute anything.

## Minimal fields

- `name`: title.
- `system`: target system.
- `action_type`: operation type.
- `risk`: integer axes from 0 to 5.

## Safety invariants

- Validate required fields before planning.
- Keep risk values within 0 to 5.
- Prefer draft and dry-run routes for human-facing operations.
- Require explicit review for public or high-risk operations.
- Require rollback notes for destructive operations.
- Future real adapters must re-check manifest hash and approval state.

## Example

```json
{
  "name": "Create draft PR",
  "system": "github",
  "action_type": "open_pr",
  "approved": true,
  "reversible": true,
  "rollback": "close_pr",
  "risk": {"ip": 1, "reputation": 1}
}
```
