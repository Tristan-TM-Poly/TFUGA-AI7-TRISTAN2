"""GitHub dry-run connector plan.

This class does not call GitHub. It converts an approved/reviewable manifest into
an execution plan that a real connector could later implement safely.
"""

from __future__ import annotations

from ..manifest import ActionManifest
from .base import ConnectorPlan


class GitHubDryRunConnector:
    name = "github_dryrun"

    def plan(self, manifest: ActionManifest) -> ConnectorPlan:
        action = manifest.action
        action_type = action.action_type.lower()
        if action_type in {"create_branch", "create_file", "open_pr", "publish_release"}:
            would_call = f"github.{action_type}"
        else:
            would_call = "github.unsupported_action"

        scopes = ["contents:read"]
        if manifest.dry_run.decision.value in {"allow_auto", "needs_approval"}:
            scopes.append("contents:write_after_approval")

        notes = [
            "dry-run only: no GitHub mutation is performed by this connector",
            "real execution must re-check manifest hash and approval state",
            "public or IP-relevant actions must keep IP review in the approval trail",
        ]

        return ConnectorPlan(
            connector=self.name,
            action_name=action.name,
            would_call=would_call,
            required_scopes=scopes,
            safety_notes=notes,
        )
