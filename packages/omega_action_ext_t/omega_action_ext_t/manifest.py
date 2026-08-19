"""Action manifest compiler for Ω-ACTION-EXT-T.

The manifest layer separates user intention from execution. It builds a reviewable
packet that can be stored, tested, queued, and audited before any connector acts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from .core import ActionDNA, DryRunReport
from .policy import OAKGate


@dataclass(frozen=True)
class ActionManifest:
    """Reviewable action packet.

    A manifest is safe to create because it does not execute the action. It is the
    canonical object to pass into dry-run, approval queue, ledger, or future
    connector adapters.
    """

    action: ActionDNA
    dry_run: DryRunReport
    schema_version: str = "0.1"
    tags: list[str] = field(default_factory=list)
    m_plus: list[str] = field(default_factory=list)
    m_minus: list[str] = field(default_factory=list)

    @classmethod
    def compile(cls, action: ActionDNA, gate: OAKGate | None = None, tags: list[str] | None = None) -> "ActionManifest":
        gate = gate or OAKGate()
        return cls(action=action, dry_run=gate.dry_run(action), tags=list(tags or []))

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "tags": list(self.tags),
            "action": self.action.to_dict(),
            "dry_run": self.dry_run.to_dict(),
            "memory": {"m_plus": list(self.m_plus), "m_minus": list(self.m_minus)},
        }
        payload["manifest_hash"] = self.content_hash(payload)
        return payload

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent, sort_keys=True)

    @staticmethod
    def content_hash(payload: dict[str, Any]) -> str:
        stable = dict(payload)
        stable.pop("manifest_hash", None)
        encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return "sha256:" + sha256(encoded).hexdigest()
