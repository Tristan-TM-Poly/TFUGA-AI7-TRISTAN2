"""Connector router for dry-run planning."""

from __future__ import annotations

from .connectors import (
    CalendarDryRunConnector,
    ConnectorPlan,
    DriveDryRunConnector,
    GitHubDryRunConnector,
    GmailDryRunConnector,
)
from .manifest import ActionManifest


class ConnectorRouter:
    """Route a manifest to the matching dry-run connector.

    Unknown systems are not executed; they become review-required plans.
    """

    def plan(self, manifest: ActionManifest) -> ConnectorPlan:
        system = manifest.action.system.lower().strip()
        if system == "github":
            return GitHubDryRunConnector().plan(manifest)
        if system == "gmail":
            return GmailDryRunConnector().plan(manifest)
        if system == "calendar":
            return CalendarDryRunConnector().plan(manifest)
        if system == "drive":
            return DriveDryRunConnector().plan(manifest)
        return ConnectorPlan(
            connector="unknown_dryrun",
            action_name=manifest.action.name,
            would_call="review_required",
            required_scopes=[],
            safety_notes=[
                "unknown system: no connector selected",
                "manual review required before any future adapter is added",
            ],
        )
