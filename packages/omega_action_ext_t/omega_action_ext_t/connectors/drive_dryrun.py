"""Drive dry-run connector plan."""

from __future__ import annotations

from ..manifest import ActionManifest
from .base import ConnectorPlan


class DriveDryRunConnector:
    name = "drive_dryrun"

    def plan(self, manifest: ActionManifest) -> ConnectorPlan:
        action = manifest.action
        if action.destructive:
            would_call = "drive.block_or_require_backup"
        elif action.action_type.lower() in {"create_file", "create_folder", "write_manifest"}:
            would_call = f"drive.{action.action_type.lower()}_after_approval"
        else:
            would_call = "drive.review_required"

        return ConnectorPlan(
            connector=self.name,
            action_name=action.name,
            would_call=would_call,
            required_scopes=["drive.file_after_approval"],
            safety_notes=[
                "dry-run only: no Drive mutation is performed",
                "avoid broad drive scopes unless strictly necessary",
                "destructive actions require backup and rollback notes",
            ],
        )
