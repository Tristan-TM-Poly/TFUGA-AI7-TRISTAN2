"""Calendar dry-run connector plan."""

from __future__ import annotations

from ..manifest import ActionManifest
from .base import ConnectorPlan


class CalendarDryRunConnector:
    name = "calendar_dryrun"

    def plan(self, manifest: ActionManifest) -> ConnectorPlan:
        action = manifest.action
        timezone = action.metadata.get("timezone") if action.metadata else None
        notes = [
            "dry-run only: no calendar mutation is performed",
            "timezone metadata must be present before real scheduling",
            "invited humans require review before invitations are sent",
        ]
        if not timezone:
            notes.append("missing timezone: keep in review queue")

        return ConnectorPlan(
            connector=self.name,
            action_name=action.name,
            would_call="calendar.create_event_after_approval",
            required_scopes=["calendar.events_after_approval"],
            safety_notes=notes,
        )
