from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AdaptiveBudget:
    """Resource-first campaign budget with no mandatory arbitrary candidate-count ceiling."""

    max_total_json_chars: int = 5_000_000
    max_candidates: int | None = None
    min_novelty: float = 0.05
    consumed_json_chars: int = 0
    accepted_candidates: int = 0

    def can_accept(self, json_chars: int, novelty: float) -> tuple[bool, str]:
        if novelty < self.min_novelty:
            return False, "novelty_floor"
        if self.max_candidates is not None and self.accepted_candidates >= self.max_candidates:
            return False, "candidate_capacity"
        if self.consumed_json_chars + int(json_chars) > self.max_total_json_chars:
            return False, "json_budget"
        return True, "accepted"

    def accept(self, json_chars: int) -> None:
        self.consumed_json_chars += int(json_chars)
        self.accepted_candidates += 1

    def snapshot(self) -> dict[str, Any]:
        return {
            "max_total_json_chars": self.max_total_json_chars,
            "max_candidates": self.max_candidates,
            "min_novelty": self.min_novelty,
            "consumed_json_chars": self.consumed_json_chars,
            "accepted_candidates": self.accepted_candidates,
        }
