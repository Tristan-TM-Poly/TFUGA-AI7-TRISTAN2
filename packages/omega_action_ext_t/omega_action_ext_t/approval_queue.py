"""Local approval queue for sovereign review."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .manifest import ActionManifest


@dataclass(frozen=True)
class ApprovalItem:
    manifest_hash: str
    title: str
    decision: str
    required_approvals: list[str]
    status: str = "pending"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_hash": self.manifest_hash,
            "title": self.title,
            "decision": self.decision,
            "required_approvals": list(self.required_approvals),
            "status": self.status,
            "notes": list(self.notes),
        }


class ApprovalQueue:
    """JSON-backed queue. It stores review items only; it never executes actions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def add_manifest(self, manifest: ActionManifest) -> ApprovalItem:
        data = manifest.to_dict()
        item = ApprovalItem(
            manifest_hash=str(data["manifest_hash"]),
            title=manifest.action.name,
            decision=manifest.dry_run.decision.value,
            required_approvals=list(manifest.dry_run.required_approvals),
        )
        items = self.items()
        items.append(item)
        self._write(items)
        return item

    def items(self) -> list[ApprovalItem]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return [ApprovalItem(**item) for item in raw]

    def _write(self, items: list[ApprovalItem]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as f:
            json.dump([item.to_dict() for item in items], f, ensure_ascii=False, indent=2, sort_keys=True)
