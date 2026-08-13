from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RepresentationAccount:
    name: str
    budget: float = 1.0
    information_gain: float = 0.0
    successes: int = 0
    failures: int = 0

    @property
    def utility(self) -> float:
        return max(0.0, self.information_gain) + 0.25 * self.successes - 0.15 * self.failures


class RepresentationMarket:
    def __init__(self, names: tuple[str, ...], *, total_budget: float = 1.0, exploration_floor: float = 0.05) -> None:
        if not names:
            raise ValueError("At least one representation is required")
        if exploration_floor * len(names) > 1.0:
            raise ValueError("Exploration floor is too large")
        self.total_budget = total_budget
        self.exploration_floor = exploration_floor
        initial = total_budget / len(names)
        self.accounts = {name: RepresentationAccount(name, initial) for name in names}

    def observe(self, name: str, *, information_gain: float, success: bool | None = None) -> None:
        acc = self.accounts[name]
        acc.information_gain += information_gain
        if success is True:
            acc.successes += 1
        elif success is False:
            acc.failures += 1

    def rebalance(self) -> dict[str, float]:
        n = len(self.accounts)
        floor_total = self.total_budget * self.exploration_floor * n
        distributable = max(0.0, self.total_budget - floor_total)
        raw = {k: 1.0 + max(0.0, a.utility) for k, a in self.accounts.items()}
        denom = sum(raw.values()) or 1.0
        for name, acc in self.accounts.items():
            acc.budget = self.total_budget * self.exploration_floor + distributable * raw[name] / denom
        return {name: acc.budget for name, acc in self.accounts.items()}
