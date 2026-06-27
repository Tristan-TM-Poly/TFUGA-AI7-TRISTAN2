"""M+ and M- memories for Ω-GAME-T."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MMinusMemory:
    """Negative memory: bugs, exploits, boredom, unfairness and OAK failures."""

    entries: list[dict[str, Any]] = field(default_factory=list)

    def record(self, reason: str, payload: dict[str, Any] | None = None) -> None:
        self.entries.append({"reason": reason, "payload": payload or {}})

    def anti_patterns(self) -> set[str]:
        return {str(entry["reason"]) for entry in self.entries}

    def last(self) -> dict[str, Any] | None:
        return self.entries[-1] if self.entries else None


@dataclass(slots=True)
class MPlusMemory:
    """Positive memory: successful quests, stable invariants and good interventions."""

    entries: list[dict[str, Any]] = field(default_factory=list)

    def record(self, result: str, payload: dict[str, Any] | None = None) -> None:
        self.entries.append({"result": result, "payload": payload or {}})

    def successful_patterns(self) -> set[str]:
        return {str(entry["result"]) for entry in self.entries}
