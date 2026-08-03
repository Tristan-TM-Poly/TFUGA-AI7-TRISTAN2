from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class ComputeBudgetPolicy:
    max_cpu_seconds: float
    max_candidates: int
    max_energy_kwh: float
    max_cost_cad: float
    reserve_fraction: float = 0.1
    max_concurrent_leases: int = 1

    def __post_init__(self) -> None:
        if min(self.max_cpu_seconds, self.max_energy_kwh, self.max_cost_cad) < 0:
            raise ValueError("budget limits must be nonnegative")
        if self.max_candidates < 0 or self.max_concurrent_leases < 1:
            raise ValueError("candidate and lease limits invalid")
        if not 0 <= self.reserve_fraction < 1:
            raise ValueError("reserve_fraction must be in [0, 1)")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ComputeObservation:
    work_id: str
    category: str
    cpu_seconds: float
    candidates: int
    energy_kwh: float
    cost_cad: float
    evidence_value: float

    def __post_init__(self) -> None:
        if not self.work_id or not self.category:
            raise ValueError("work_id and category are required")
        if min(self.cpu_seconds, self.candidates, self.energy_kwh, self.cost_cad, self.evidence_value) < 0:
            raise ValueError("observations must be nonnegative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BudgetLedger:
    def __init__(self, policy: ComputeBudgetPolicy):
        self.policy = policy
        self._observations: list[ComputeObservation] = []
        self._ids: set[str] = set()

    @property
    def observations(self) -> tuple[ComputeObservation, ...]:
        return tuple(self._observations)

    def totals(self) -> dict[str, float | int]:
        return {
            "cpu_seconds": sum(item.cpu_seconds for item in self._observations),
            "candidates": sum(item.candidates for item in self._observations),
            "energy_kwh": sum(item.energy_kwh for item in self._observations),
            "cost_cad": sum(item.cost_cad for item in self._observations),
            "evidence_value": sum(item.evidence_value for item in self._observations),
        }

    def _effective_limits(self) -> dict[str, float | int]:
        factor = 1.0 - self.policy.reserve_fraction
        return {
            "cpu_seconds": self.policy.max_cpu_seconds * factor,
            "candidates": int(self.policy.max_candidates * factor),
            "energy_kwh": self.policy.max_energy_kwh * factor,
            "cost_cad": self.policy.max_cost_cad * factor,
        }

    def can_accept(self, observation: ComputeObservation) -> tuple[bool, tuple[str, ...]]:
        if observation.work_id in self._ids:
            return False, ("duplicate work_id",)
        totals = self.totals()
        limits = self._effective_limits()
        reasons = []
        for key in ("cpu_seconds", "candidates", "energy_kwh", "cost_cad"):
            if totals[key] + getattr(observation, key) > limits[key]:
                reasons.append(f"{key} reserve boundary exceeded")
        return not reasons, tuple(reasons)

    def record(self, observation: ComputeObservation) -> None:
        allowed, reasons = self.can_accept(observation)
        if not allowed:
            raise ValueError("; ".join(reasons))
        self._observations.append(observation)
        self._ids.add(observation.work_id)

    def report(self) -> dict[str, Any]:
        totals = self.totals()
        limits = self._effective_limits()
        remaining = {key: max(0, limits[key] - totals[key]) for key in limits}
        utilization = {
            key: (float(totals[key]) / float(limits[key]) if limits[key] else (1.0 if totals[key] else 0.0))
            for key in limits
        }
        max_utilization = max(utilization.values(), default=0.0)
        state = "halt" if max_utilization >= 1 else "backpressure" if max_utilization >= 0.8 else "open"
        return {
            "policy": self.policy.to_dict(),
            "observations": [item.to_dict() for item in self._observations],
            "totals": totals,
            "effective_limits_after_reserve": limits,
            "remaining": remaining,
            "utilization": utilization,
            "state": state,
            "oak": {
                "cost_is_user_supplied_evidence": True,
                "financial_return_claimed": False,
                "unbounded_physical_compute_claimed": False,
                "reserve_enforced": True,
            },
        }


def rank_work_items(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = []
    for raw in items:
        item = dict(raw)
        evidence = float(item.get("expected_evidence", 0.0))
        cpu = float(item.get("expected_cpu_seconds", 0.0))
        energy = float(item.get("expected_energy_kwh", 0.0))
        cost = float(item.get("expected_cost_cad", 0.0))
        denominator = 1.0 + cpu + 3600.0 * energy + 100.0 * cost
        item["priority_score"] = evidence / denominator
        ranked.append(item)
    return sorted(ranked, key=lambda item: (-item["priority_score"], str(item.get("work_id", ""))))
