"""Connector base classes.

Connectors in this MVP are dry-run-only. A future real connector must consume an
approved manifest and write proof records; it must not bypass OAKGate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from ..manifest import ActionManifest


@dataclass(frozen=True)
class ConnectorPlan:
    connector: str
    action_name: str
    would_call: str
    required_scopes: list[str] = field(default_factory=list)
    safety_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "connector": self.connector,
            "action_name": self.action_name,
            "would_call": self.would_call,
            "required_scopes": list(self.required_scopes),
            "safety_notes": list(self.safety_notes),
        }


class DryRunConnector(Protocol):
    name: str

    def plan(self, manifest: ActionManifest) -> ConnectorPlan:
        """Return a connector plan without making external changes."""
        ...
