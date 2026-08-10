from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class RecoveryMode(str, Enum):
    REUSE = "reuse"
    REPAIR = "repair"
    REMANUFACTURE = "remanufacture"
    COMPONENT_HARVEST = "component_harvest"
    MATERIAL_RECYCLE = "material_recycle"
    ENERGY_RECOVERY = "energy_recovery"
    DISPOSAL = "disposal"


PRESERVATION_RANK: dict[RecoveryMode, int] = {
    RecoveryMode.REUSE: 7,
    RecoveryMode.REPAIR: 6,
    RecoveryMode.REMANUFACTURE: 5,
    RecoveryMode.COMPONENT_HARVEST: 4,
    RecoveryMode.MATERIAL_RECYCLE: 3,
    RecoveryMode.ENERGY_RECOVERY: 2,
    RecoveryMode.DISPOSAL: 1,
}


@dataclass(frozen=True, slots=True)
class Material:
    name: str
    unit_value_per_kg: float
    purity: float = 1.0
    hazard_class: str | None = None

    def __post_init__(self) -> None:
        if self.unit_value_per_kg < 0:
            raise ValueError("unit_value_per_kg must be non-negative")
        if not 0 <= self.purity <= 1:
            raise ValueError("purity must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class Component:
    component_id: str
    name: str
    mass_kg: float
    material_fractions: dict[str, float]
    reuse_value: float
    functional_probability: float = 1.0
    hazardous: bool = False
    disassembly_cost: float = 0.0
    disassembly_energy_kwh: float = 0.0
    contamination: float = 0.0
    expected_future_cycles: float = 1.0

    def __post_init__(self) -> None:
        if self.mass_kg <= 0:
            raise ValueError("mass_kg must be positive")
        if self.reuse_value < 0:
            raise ValueError("reuse_value must be non-negative")
        if not 0 <= self.functional_probability <= 1:
            raise ValueError("functional_probability must be in [0, 1]")
        if not 0 <= self.contamination <= 1:
            raise ValueError("contamination must be in [0, 1]")
        if self.expected_future_cycles < 0:
            raise ValueError("expected_future_cycles must be non-negative")
        total = sum(self.material_fractions.values())
        if any(v < 0 for v in self.material_fractions.values()):
            raise ValueError("material fractions must be non-negative")
        if not 0.999 <= total <= 1.001:
            raise ValueError("material fractions must sum to 1")


@dataclass(frozen=True, slots=True)
class RecoveryRoute:
    mode: RecoveryMode
    process_cost: float = 0.0
    energy_kwh: float = 0.0
    risk: float = 0.0
    externality_penalty: float = 0.0
    output_quality: float = 1.0
    retained_mass_fraction: float = 1.0
    requires_certified_process: bool = False

    def __post_init__(self) -> None:
        if self.process_cost < 0 or self.energy_kwh < 0 or self.externality_penalty < 0:
            raise ValueError("cost, energy and externality values must be non-negative")
        if not 0 <= self.risk <= 1:
            raise ValueError("risk must be in [0, 1]")
        if not 0 <= self.output_quality <= 1:
            raise ValueError("output_quality must be in [0, 1]")
        if not 0 <= self.retained_mass_fraction <= 1:
            raise ValueError("retained_mass_fraction must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class RouteEvaluation:
    component_id: str
    mode: RecoveryMode
    recovered_value: float
    total_cost: float
    retained_mass_kg: float
    score: float
    dry_run_only: bool
    warnings: tuple[str, ...] = ()


@dataclass(slots=True)
class RecoveryPlan:
    evaluations: list[RouteEvaluation] = field(default_factory=list)

    @property
    def total_score(self) -> float:
        return sum(item.score for item in self.evaluations)

    @property
    def recovered_value(self) -> float:
        return sum(item.recovered_value for item in self.evaluations)

    @property
    def retained_mass_kg(self) -> float:
        return sum(item.retained_mass_kg for item in self.evaluations)

    @property
    def dry_run_only(self) -> bool:
        return any(item.dry_run_only for item in self.evaluations)

    def modes(self) -> tuple[str, ...]:
        return tuple(item.mode.value for item in self.evaluations)


@dataclass(frozen=True, slots=True)
class Hyperedge:
    relation: str
    members: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.members) < 2:
            raise ValueError("hyperedge requires at least two members")


@dataclass(slots=True)
class ResourceGraph:
    components: dict[str, Component] = field(default_factory=dict)
    hyperedges: list[Hyperedge] = field(default_factory=list)

    def add_component(self, component: Component) -> None:
        if component.component_id in self.components:
            raise ValueError(f"duplicate component_id: {component.component_id}")
        self.components[component.component_id] = component

    def add_hyperedge(self, relation: str, members: Iterable[str]) -> None:
        member_tuple = tuple(members)
        missing = [member for member in member_tuple if member not in self.components]
        if missing:
            raise KeyError(f"unknown component ids: {missing}")
        self.hyperedges.append(Hyperedge(relation=relation, members=member_tuple))

    def total_mass_kg(self) -> float:
        return sum(c.mass_kg for c in self.components.values())

    def disassembly_cut_value(self, component_ids: Iterable[str]) -> float:
        selected = [self.components[cid] for cid in component_ids]
        return sum(c.reuse_value * c.functional_probability for c in selected)
