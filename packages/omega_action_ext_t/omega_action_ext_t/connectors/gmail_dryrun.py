"""Gmail dry-run connector plan.

This connector never sends or creates messages. It only describes the safe plan a
future real adapter would need to follow.
"""

from __future__ import annotations

from ..manifest import ActionManifest
from .base import ConnectorPlan


class GmailDryRunConnector:
    name = "gmail_dryrun"

    def plan(self, manifest: ActionManifest) -> ConnectorPlan:
        action = manifest.action
        action_type = action.action_type.lower()
        if action_type == "send_email" and manifest.dry_run.decision.value == "allow_draft":
            would_call = "gmail.create_draft"
        elif action_type == "create_draft":
            would_call = "gmail.create_draft"
        else:
            would_call = "gmail.review_required"

        return ConnectorPlan(
            connector=self.name,
            action_name=action.name,
            would_call=would_call,
            required_scopes=["gmail.compose_after_approval"],
            safety_notes=[
                "dry-run only: no Gmail mutation is performed",
                "final send requires explicit confirmation",
                "recipient and subject should be rendered for review",
            ],
        )
