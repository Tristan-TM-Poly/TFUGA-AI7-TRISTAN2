from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import math
from typing import Any, Iterable, Mapping

from .models import EpistemicStatus, PhaseRecord


@dataclass(frozen=True, slots=True)
class PhaseTransition:
    source: str
    target: str
    barrier_j_mol: float
    driving_force_j_mol: float = 0.0
    characteristic_time_s: float | None = None
    reversible: bool = False
    uncertainty_j_mol: float | None = None
    conditions: Mapping[str, Any] = field(default_factory=dict)
    mechanism: str | None = None
    status: EpistemicStatus = EpistemicStatus.MODEL_EXTRAPOLATION

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise ValueError("Phase transition source and target must differ")
        if self.barrier_j_mol < 0:
            raise ValueError("Transition barrier cannot be negative")
        if self.characteristic_time_s is not None and self.characteristic_time_s < 0:
            raise ValueError("Characteristic time cannot be negative")
        if self.uncertainty_j_mol is not None and self.uncertainty_j_mol < 0:
            raise ValueError("Barrier uncertainty cannot be negative")

    def effective_cost(self, *, temperature_k: float | None = None) -> float:
        cost = max(0.0, self.barrier_j_mol + max(0.0, self.driving_force_j_mol))
        if temperature_k is None:
            return cost
        if temperature_k <= 0:
            raise ValueError("Temperature must be positive")
        gas_constant = 8.314462618
        return cost / (gas_constant * temperature_k)

    def arrhenius_factor(self, temperature_k: float) -> float:
        return math.exp(-self.effective_cost(temperature_k=temperature_k))

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "barrier_j_mol": self.barrier_j_mol,
            "driving_force_j_mol": self.driving_force_j_mol,
            "characteristic_time_s": self.characteristic_time_s,
            "reversible": self.reversible,
            "uncertainty_j_mol": self.uncertainty_j_mol,
            "conditions": dict(self.conditions),
            "mechanism": self.mechanism,
            "status": self.status.value,
        }


class PhaseGraph:
    def __init__(
        self,
        phases: Iterable[PhaseRecord] = (),
        transitions: Iterable[PhaseTransition] = (),
    ) -> None:
        self.phases = {phase.name: phase for phase in phases}
        self.transitions: list[PhaseTransition] = []
        for transition in transitions:
            self.add_transition(transition)

    def add_phase(self, phase: PhaseRecord) -> None:
        if phase.name in self.phases:
            raise ValueError(f"Duplicate phase: {phase.name}")
        self.phases[phase.name] = phase

    def add_transition(self, transition: PhaseTransition) -> None:
        missing = [
            name for name in (transition.source, transition.target) if name not in self.phases
        ]
        if missing:
            raise KeyError(f"Unknown phase(s): {missing}")
        self.transitions.append(transition)
        if transition.reversible:
            self.transitions.append(
                PhaseTransition(
                    source=transition.target,
                    target=transition.source,
                    barrier_j_mol=max(
                        0.0,
                        transition.barrier_j_mol - transition.driving_force_j_mol,
                    ),
                    driving_force_j_mol=-transition.driving_force_j_mol,
                    characteristic_time_s=transition.characteristic_time_s,
                    reversible=False,
                    uncertainty_j_mol=transition.uncertainty_j_mol,
                    conditions=transition.conditions,
                    mechanism=transition.mechanism,
                    status=transition.status,
                )
            )

    def outgoing(self, phase: str) -> tuple[PhaseTransition, ...]:
        if phase not in self.phases:
            raise KeyError(phase)
        return tuple(
            sorted(
                (item for item in self.transitions if item.source == phase),
                key=lambda item: (item.target, item.barrier_j_mol),
            )
        )

    def minimum_barrier_path(
        self,
        source: str,
        target: str,
        *,
        temperature_k: float | None = None,
    ) -> tuple[tuple[str, ...], float] | None:
        if source not in self.phases or target not in self.phases:
            raise KeyError("Source and target phases must exist")
        queue: list[tuple[float, str, tuple[str, ...]]] = [(0.0, source, (source,))]
        best = {source: 0.0}
        while queue:
            cost, current, path = heapq.heappop(queue)
            if cost > best[current]:
                continue
            if current == target:
                return path, cost
            for transition in self.outgoing(current):
                candidate = cost + transition.effective_cost(temperature_k=temperature_k)
                if candidate < best.get(transition.target, float("inf")):
                    best[transition.target] = candidate
                    heapq.heappush(
                        queue,
                        (candidate, transition.target, (*path, transition.target)),
                    )
        return None

    def metastability_index(self, phase: str) -> float:
        outgoing = self.outgoing(phase)
        if not outgoing:
            return 1.0
        minimum_barrier = min(item.barrier_j_mol for item in outgoing)
        driving = max(abs(item.driving_force_j_mol) for item in outgoing)
        scale = max(1.0, minimum_barrier + driving)
        return max(0.0, min(1.0, minimum_barrier / scale))

    def to_dict(self) -> dict[str, Any]:
        return {
            "phases": [self.phases[name].to_dict() for name in sorted(self.phases)],
            "transitions": [
                item.to_dict()
                for item in sorted(
                    self.transitions,
                    key=lambda transition: (
                        transition.source,
                        transition.target,
                        transition.barrier_j_mol,
                    ),
                )
            ],
        }
