from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class PortfolioArm:
    name: str
    purpose: str
    pulls: int = 0
    reward_sum: float = 0.0
    compute_units: float = 0.0

    @property
    def mean_reward(self) -> float:
        return 0.0 if self.pulls == 0 else self.reward_sum / self.pulls

    @property
    def efficiency(self) -> float:
        return 0.0 if self.compute_units == 0 else self.reward_sum / self.compute_units

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["mean_reward"] = round(self.mean_reward, 12)
        payload["efficiency"] = round(self.efficiency, 12)
        return payload


DEFAULT_ARMS = (
    ("prestige", "record-oriented external campaigns"),
    ("research", "specialized families and mathematical evidence"),
    ("product", "public engineering primes, software and certification"),
)


class PortfolioAllocator:
    """Deterministic UCB1 allocator; rewards are evidence signals, not money forecasts."""

    def __init__(self, exploration: float = math.sqrt(2.0)):
        if exploration < 0:
            raise ValueError("exploration must be non-negative")
        self.exploration = exploration
        self.arms = {name: PortfolioArm(name, purpose) for name, purpose in DEFAULT_ARMS}
        self.total_pulls = 0

    def choose(self) -> str:
        for name in sorted(self.arms):
            if self.arms[name].pulls == 0:
                return name
        scores = {
            name: arm.mean_reward
            + self.exploration * math.sqrt(math.log(self.total_pulls) / arm.pulls)
            for name, arm in self.arms.items()
        }
        return max(sorted(scores), key=lambda name: scores[name])

    def observe(self, name: str, reward: float, compute_units: float = 1.0) -> None:
        if name not in self.arms:
            raise KeyError(name)
        if compute_units <= 0:
            raise ValueError("compute_units must be positive")
        arm = self.arms[name]
        arm.pulls += 1
        arm.reward_sum += float(reward)
        arm.compute_units += float(compute_units)
        self.total_pulls += 1

    def recommended_weights(self) -> dict[str, float]:
        raw = {
            name: max(0.01, arm.efficiency if arm.pulls else 0.01)
            for name, arm in self.arms.items()
        }
        total = sum(raw.values())
        return {name: round(value / total, 8) for name, value in sorted(raw.items())}

    def report(self) -> dict[str, Any]:
        return {
            "policy": "deterministic_ucb1_evidence_allocator",
            "exploration": self.exploration,
            "total_pulls": self.total_pulls,
            "arms": [self.arms[name].to_dict() for name in sorted(self.arms)],
            "recommended_weights": self.recommended_weights(),
            "claims": {
                "financial_return_predicted": False,
                "record_probability_certified": False,
                "allocation_is_advisory": True,
            },
        }
