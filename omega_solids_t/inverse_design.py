from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
from typing import Any, Callable, Iterable, Mapping, Sequence

from .genome import SolidGenome
from .invariants import build_signature
from .models import PropertyRecord
from .oak import OAKReport, run_oak_gate


@dataclass(frozen=True, slots=True)
class PropertyObjective:
    property_name: str
    target: float
    unit: str
    tolerance: float
    weight: float = 1.0
    mode: str = "target"  # target, maximize, minimize

    def __post_init__(self) -> None:
        if not self.property_name.strip():
            raise ValueError("Objective property name cannot be empty")
        if self.tolerance <= 0:
            raise ValueError("Objective tolerance must be positive")
        if self.weight < 0:
            raise ValueError("Objective weight cannot be negative")
        if self.mode not in {"target", "maximize", "minimize"}:
            raise ValueError("Objective mode must be target, maximize, or minimize")

    def score(self, record: PropertyRecord | None) -> float:
        if record is None or record.quantity.unit != self.unit:
            return 0.0
        value = record.quantity.value
        if self.mode == "target":
            return math.exp(-abs(value - self.target) / self.tolerance)
        if self.mode == "maximize":
            scale = max(abs(self.target), self.tolerance)
            return 1.0 / (1.0 + math.exp(-(value - self.target) / scale))
        scale = max(abs(self.target), self.tolerance)
        return 1.0 / (1.0 + math.exp((value - self.target) / scale))


@dataclass(frozen=True, slots=True)
class DesignConstraint:
    name: str
    predicate: Callable[[SolidGenome], bool]
    description: str
    hard: bool = True
    penalty: float = 0.2

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.description.strip():
            raise ValueError("Constraint name and description are required")
        if not 0 <= self.penalty <= 1:
            raise ValueError("Constraint penalty must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    genome: SolidGenome
    objective_score: float
    oak_score: float
    total_score: float
    hard_violations: tuple[str, ...]
    soft_violations: tuple[str, ...]
    objective_breakdown: Mapping[str, float]
    oak_report: OAKReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "genome_id": self.genome.identifier,
            "objective_score": self.objective_score,
            "oak_score": self.oak_score,
            "total_score": self.total_score,
            "hard_violations": list(self.hard_violations),
            "soft_violations": list(self.soft_violations),
            "objective_breakdown": dict(self.objective_breakdown),
            "oak_status": self.oak_report.status.value,
            "cvcd_signature": build_signature(self.genome).to_dict(),
        }


class SolidCompiler:
    """Rank known or generated genomes against explicit goals and constraints."""

    def __init__(
        self,
        objectives: Sequence[PropertyObjective],
        constraints: Sequence[DesignConstraint] = (),
        *,
        oak_weight: float = 0.35,
    ) -> None:
        if not objectives:
            raise ValueError("At least one objective is required")
        if not 0 <= oak_weight <= 1:
            raise ValueError("OAK weight must be within [0, 1]")
        self.objectives = tuple(objectives)
        self.constraints = tuple(constraints)
        self.oak_weight = oak_weight

    def evaluate(self, genome: SolidGenome) -> RankedCandidate:
        property_map = genome.property_map()
        breakdown = {
            objective.property_name: objective.score(
                property_map.get(objective.property_name)
            )
            for objective in self.objectives
        }
        total_weight = sum(objective.weight for objective in self.objectives)
        objective_score = (
            sum(
                objective.weight * breakdown[objective.property_name]
                for objective in self.objectives
            )
            / total_weight
            if total_weight > 0
            else 0.0
        )
        hard: list[str] = []
        soft: list[str] = []
        penalty_factor = 1.0
        for constraint in self.constraints:
            if constraint.predicate(genome):
                continue
            if constraint.hard:
                hard.append(constraint.name)
            else:
                soft.append(constraint.name)
                penalty_factor *= 1.0 - constraint.penalty
        oak = run_oak_gate(genome)
        blended = (1 - self.oak_weight) * objective_score + self.oak_weight * oak.score
        total = 0.0 if hard else blended * penalty_factor
        return RankedCandidate(
            genome,
            objective_score,
            oak.score,
            total,
            tuple(hard),
            tuple(soft),
            breakdown,
            oak,
        )

    def rank(self, genomes: Iterable[SolidGenome]) -> tuple[RankedCandidate, ...]:
        candidates = [self.evaluate(genome) for genome in genomes]
        return tuple(
            sorted(
                candidates,
                key=lambda candidate: (
                    bool(candidate.hard_violations),
                    -candidate.total_score,
                    candidate.genome.identifier,
                ),
            )
        )


def maximum_porosity(value: float) -> DesignConstraint:
    if not 0 <= value < 1:
        raise ValueError("Maximum porosity must be within [0, 1)")
    return DesignConstraint(
        "maximum_porosity",
        lambda genome: float(genome.geometry.get("porosity", 0.0)) <= value,
        f"Porosity must not exceed {value}.",
    )


def allowed_families(*families: str) -> DesignConstraint:
    allowed = {family.strip().lower() for family in families if family.strip()}
    if not allowed:
        raise ValueError("At least one allowed family is required")
    return DesignConstraint(
        "allowed_families",
        lambda genome: any(token in genome.family.lower() for token in allowed),
        f"Family must match one of {sorted(allowed)}.",
    )


def require_process_step(token: str, *, hard: bool = False) -> DesignConstraint:
    normalized = token.strip().lower()
    if not normalized:
        raise ValueError("Process token cannot be empty")
    return DesignConstraint(
        f"require_process:{normalized}",
        lambda genome: any(
            normalized in str(step.get("name", step.get("operation", ""))).lower()
            for step in genome.process
        ),
        f"Process must contain a step matching {normalized!r}.",
        hard=hard,
        penalty=0.15,
    )
