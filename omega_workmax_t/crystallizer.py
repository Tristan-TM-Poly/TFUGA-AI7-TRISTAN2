from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CrystallizationDecision:
    mode: str
    debt: int
    debt_ratio: float
    expansion_share: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "debt": self.debt,
            "debt_ratio": self.debt_ratio,
            "expansion_share": self.expansion_share,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class CrystallizationGovernor:
    soft_debt_ratio: float = 0.25
    hard_debt_ratio: float = 0.50

    def __post_init__(self) -> None:
        if not 0.0 <= self.soft_debt_ratio < self.hard_debt_ratio <= 1.0:
            raise ValueError("debt ratios must satisfy 0 <= soft < hard <= 1")

    def decide(self, *, started: int, crystallized: int) -> CrystallizationDecision:
        if started < 0 or crystallized < 0:
            raise ValueError("counts cannot be negative")
        debt = max(0, started - crystallized)
        debt_ratio = debt / max(1, started)
        if debt_ratio >= self.hard_debt_ratio:
            return CrystallizationDecision(
                "CRYSTALLIZE",
                debt,
                debt_ratio,
                0.10,
                ("crystallization debt crossed the hard ratio", "prefer tests/docs/API/benchmark/closure over new branches"),
            )
        if debt_ratio >= self.soft_debt_ratio:
            return CrystallizationDecision(
                "BALANCED",
                debt,
                debt_ratio,
                0.40,
                ("crystallization debt crossed the soft ratio", "allow expansion only when it unlocks closure or evidence"),
            )
        return CrystallizationDecision(
            "EXPAND",
            debt,
            debt_ratio,
            0.75,
            ("crystallization debt is currently controlled", "expansion remains subordinate to OAK and capacity backpressure"),
        )
