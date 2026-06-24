"""Bayes-Tristan prioritization engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .science_card import ScienceCard, cards_from_mappings


class BayesTristanEngine:
    """Rank, filter and summarize ScienceCards.

    The first implementation is deliberately transparent. It is not a claim
    that the weights are final; it is a minimal OAK-testable scoring layer.
    """

    def __init__(self, cards: Iterable[ScienceCard] | None = None) -> None:
        self.cards: list[ScienceCard] = list(cards or [])

    def add(self, card: ScienceCard) -> None:
        self.cards.append(card)

    def ranked(self) -> list[ScienceCard]:
        return sorted(self.cards, key=lambda card: card.priority(), reverse=True)

    def top(self, n: int = 10) -> list[ScienceCard]:
        return self.ranked()[:n]

    def by_branch(self, branch: str) -> list[ScienceCard]:
        return [card for card in self.ranked() if card.branch == branch]

    def oak_gaps(self) -> list[ScienceCard]:
        """Cards mature enough to require explicit tests, but missing them."""

        return [card for card in self.ranked() if card.needs_oak_review()]

    def next_actions(self, n: int = 10) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        for card in self.ranked():
            if card.next_actions:
                actions.append(
                    {
                        "id": card.id,
                        "name": card.name,
                        "priority": round(card.priority(), 4),
                        "status_oak": card.status_oak.value,
                        "next_action": card.next_actions[0],
                    }
                )
            if len(actions) >= n:
                break
        return actions

    def portfolio_report(self) -> dict[str, Any]:
        ranked = self.ranked()
        branches: dict[str, int] = {}
        statuses: dict[str, int] = {}
        for card in ranked:
            branches[card.branch] = branches.get(card.branch, 0) + 1
            statuses[card.status_oak.value] = statuses.get(card.status_oak.value, 0) + 1
        return {
            "total_cards": len(ranked),
            "branches": branches,
            "statuses": statuses,
            "top_cards": [
                {
                    "id": card.id,
                    "name": card.name,
                    "priority": round(card.priority(), 4),
                    "branch": card.branch,
                    "status_oak": card.status_oak.value,
                }
                for card in ranked[:10]
            ],
            "oak_gaps": [
                {
                    "id": card.id,
                    "name": card.name,
                    "reason": "Omega_2+ card has no explicit tests",
                }
                for card in self.oak_gaps()
            ],
            "next_actions": self.next_actions(10),
        }

    @classmethod
    def from_json_path(cls, path: str | Path) -> "BayesTristanEngine":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        items = data["cards"] if isinstance(data, dict) and "cards" in data else data
        return cls(cards_from_mappings(items))

    @classmethod
    def from_yaml_path(cls, path: str | Path) -> "BayesTristanEngine":
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError("YAML loading requires PyYAML; use from_json_path or install PyYAML.") from exc
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        items = data["cards"] if isinstance(data, dict) and "cards" in data else data
        return cls(cards_from_mappings(items))
