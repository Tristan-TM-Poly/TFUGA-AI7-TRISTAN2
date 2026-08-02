from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence


class EpistemicStatus(str, Enum):
    """Ordered status labels used by the OAK gate.

    The enum is deliberately explicit: a simulated value must never silently
    become a measured or independently validated value.
    """

    MEASURED = "measured"
    ESTABLISHED_THEORY = "established_theory"
    SIMULATED = "simulated"
    MODEL_EXTRAPOLATION = "model_extrapolation"
    FERTILE_HYPOTHESIS = "fertile_hypothesis"
    PROPOSED_DESIGN = "proposed_design"
    FABRICATED_PROTOTYPE = "fabricated_prototype"
    INDEPENDENTLY_VALIDATED = "independently_validated"


class Dimensionality(str, Enum):
    ZERO_D = "0D"
    ONE_D = "1D"
    TWO_D = "2D"
    THREE_D = "3D"
    TIME_PROGRAMMED = "4D-design"
    INFORMATIONAL_ND = "nD-information"


class OrderClass(str, Enum):
    PERIODIC_CRYSTAL = "periodic_crystal"
    QUASICRYSTAL = "quasicrystal"
    AMORPHOUS = "amorphous"
    SEMICRYSTALLINE = "semicrystalline"
    POLYCRYSTALLINE = "polycrystalline"
    HIERARCHICAL = "hierarchical"
    GRANULAR = "granular"
    UNKNOWN = "unknown"


class BondClass(str, Enum):
    IONIC = "ionic"
    COVALENT = "covalent"
    METALLIC = "metallic"
    MOLECULAR = "molecular"
    HYDROGEN_BONDED = "hydrogen_bonded"
    POLYMERIC = "polymeric"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class DefectKind(str, Enum):
    VACANCY = "vacancy"
    INTERSTITIAL = "interstitial"
    SUBSTITUTION = "substitution"
    DISLOCATION = "dislocation"
    STACKING_FAULT = "stacking_fault"
    GRAIN_BOUNDARY = "grain_boundary"
    PORE = "pore"
    INCLUSION = "inclusion"
    CRACK = "crack"
    RESIDUAL_STRESS = "residual_stress"
    CHEMICAL_DISORDER = "chemical_disorder"
    ELECTRONIC = "electronic"
    TOPOLOGICAL = "topological"
    DELAMINATION = "delamination"
    OTHER = "other"


class PropertyDomain(str, Enum):
    MECHANICAL = "mechanical"
    THERMAL = "thermal"
    ELECTRICAL = "electrical"
    MAGNETIC = "magnetic"
    OPTICAL = "optical"
    CHEMICAL = "chemical"
    IONIC = "ionic"
    ACOUSTIC = "acoustic"
    BIOLOGICAL = "biological"
    ECONOMIC = "economic"
    DURABILITY = "durability"
    GEOMETRIC = "geometric"


class GateStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class Quantity:
    """Numerical value with unit, provenance and uncertainty.

    This is not a complete units library. It prevents the most damaging loss of
    metadata while keeping the package dependency-free.
    """

    value: float
    unit: str
    uncertainty: float | None = None
    status: EpistemicStatus = EpistemicStatus.MODEL_EXTRAPOLATION
    source: str | None = None
    method: str | None = None
    conditions: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.unit.strip():
            raise ValueError("Quantity.unit cannot be empty")
        if self.uncertainty is not None and self.uncertainty < 0:
            raise ValueError("Quantity.uncertainty cannot be negative")

    def relative_uncertainty(self) -> float | None:
        if self.uncertainty is None:
            return None
        if self.value == 0:
            return float("inf") if self.uncertainty else 0.0
        return abs(self.uncertainty / self.value)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        payload["conditions"] = dict(self.conditions)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Quantity":
        return cls(
            value=float(payload["value"]),
            unit=str(payload["unit"]),
            uncertainty=(
                None
                if payload.get("uncertainty") is None
                else float(payload["uncertainty"])
            ),
            status=EpistemicStatus(
                payload.get("status", EpistemicStatus.MODEL_EXTRAPOLATION.value)
            ),
            source=payload.get("source"),
            method=payload.get("method"),
            conditions=dict(payload.get("conditions", {})),
        )


@dataclass(frozen=True, slots=True)
class CompositionComponent:
    species: str
    fraction: float
    basis: str = "atomic"
    role: str | None = None
    uncertainty: float | None = None

    def __post_init__(self) -> None:
        if not self.species.strip():
            raise ValueError("Composition species cannot be empty")
        if self.fraction < 0:
            raise ValueError("Composition fraction cannot be negative")
        if self.uncertainty is not None and self.uncertainty < 0:
            raise ValueError("Composition uncertainty cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CompositionComponent":
        return cls(
            species=str(payload["species"]),
            fraction=float(payload["fraction"]),
            basis=str(payload.get("basis", "atomic")),
            role=payload.get("role"),
            uncertainty=(
                None
                if payload.get("uncertainty") is None
                else float(payload["uncertainty"])
            ),
        )


@dataclass(frozen=True, slots=True)
class BondContribution:
    kind: BondClass
    weight: float
    note: str | None = None

    def __post_init__(self) -> None:
        if self.weight < 0:
            raise ValueError("Bond weight cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind.value, "weight": self.weight, "note": self.note}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "BondContribution":
        return cls(
            kind=BondClass(str(payload["kind"])),
            weight=float(payload["weight"]),
            note=payload.get("note"),
        )


@dataclass(frozen=True, slots=True)
class DefectRecord:
    kind: DefectKind
    density: Quantity | None = None
    geometry: Mapping[str, Any] = field(default_factory=dict)
    orientation: Sequence[float] | None = None
    mobility: float | None = None
    formation_energy: Quantity | None = None
    criticality: float = 0.0
    function: str | None = None
    status: EpistemicStatus = EpistemicStatus.MODEL_EXTRAPOLATION

    def __post_init__(self) -> None:
        if not 0 <= self.criticality <= 1:
            raise ValueError("Defect criticality must be within [0, 1]")
        if self.mobility is not None and self.mobility < 0:
            raise ValueError("Defect mobility cannot be negative")
        if self.orientation is not None and len(self.orientation) not in (2, 3, 4):
            raise ValueError("Defect orientation must have 2, 3, or 4 components")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "density": None if self.density is None else self.density.to_dict(),
            "geometry": dict(self.geometry),
            "orientation": None if self.orientation is None else list(self.orientation),
            "mobility": self.mobility,
            "formation_energy": (
                None if self.formation_energy is None else self.formation_energy.to_dict()
            ),
            "criticality": self.criticality,
            "function": self.function,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DefectRecord":
        return cls(
            kind=DefectKind(str(payload["kind"])),
            density=(
                None
                if payload.get("density") is None
                else Quantity.from_dict(payload["density"])
            ),
            geometry=dict(payload.get("geometry", {})),
            orientation=payload.get("orientation"),
            mobility=(None if payload.get("mobility") is None else float(payload["mobility"])),
            formation_energy=(
                None
                if payload.get("formation_energy") is None
                else Quantity.from_dict(payload["formation_energy"])
            ),
            criticality=float(payload.get("criticality", 0.0)),
            function=payload.get("function"),
            status=EpistemicStatus(
                payload.get("status", EpistemicStatus.MODEL_EXTRAPOLATION.value)
            ),
        )


@dataclass(frozen=True, slots=True)
class InterfaceRecord:
    name: str
    between: tuple[str, str]
    thickness: Quantity | None = None
    energy: Quantity | None = None
    charge_density: Quantity | None = None
    coherency: str | None = None
    orientation_relationship: str | None = None
    properties: Mapping[str, Quantity] = field(default_factory=dict)
    defects: tuple[DefectRecord, ...] = ()
    status: EpistemicStatus = EpistemicStatus.MODEL_EXTRAPOLATION

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Interface name cannot be empty")
        if len(self.between) != 2 or not all(part.strip() for part in self.between):
            raise ValueError("Interface.between must identify exactly two non-empty regions")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "between": list(self.between),
            "thickness": None if self.thickness is None else self.thickness.to_dict(),
            "energy": None if self.energy is None else self.energy.to_dict(),
            "charge_density": (
                None if self.charge_density is None else self.charge_density.to_dict()
            ),
            "coherency": self.coherency,
            "orientation_relationship": self.orientation_relationship,
            "properties": {name: value.to_dict() for name, value in self.properties.items()},
            "defects": [record.to_dict() for record in self.defects],
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "InterfaceRecord":
        return cls(
            name=str(payload["name"]),
            between=tuple(payload["between"]),  # type: ignore[arg-type]
            thickness=(
                None
                if payload.get("thickness") is None
                else Quantity.from_dict(payload["thickness"])
            ),
            energy=(
                None
                if payload.get("energy") is None
                else Quantity.from_dict(payload["energy"])
            ),
            charge_density=(
                None
                if payload.get("charge_density") is None
                else Quantity.from_dict(payload["charge_density"])
            ),
            coherency=payload.get("coherency"),
            orientation_relationship=payload.get("orientation_relationship"),
            properties={
                str(name): Quantity.from_dict(value)
                for name, value in payload.get("properties", {}).items()
            },
            defects=tuple(
                DefectRecord.from_dict(record) for record in payload.get("defects", [])
            ),
            status=EpistemicStatus(
                payload.get("status", EpistemicStatus.MODEL_EXTRAPOLATION.value)
            ),
        )


@dataclass(frozen=True, slots=True)
class PhaseRecord:
    name: str
    fraction: float
    order: OrderClass
    space_group: str | None = None
    lattice_parameters: Mapping[str, Quantity] = field(default_factory=dict)
    stability_window: Mapping[str, Any] = field(default_factory=dict)
    status: EpistemicStatus = EpistemicStatus.MODEL_EXTRAPOLATION

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Phase name cannot be empty")
        if not 0 <= self.fraction <= 1:
            raise ValueError("Phase fraction must be within [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "fraction": self.fraction,
            "order": self.order.value,
            "space_group": self.space_group,
            "lattice_parameters": {
                name: value.to_dict() for name, value in self.lattice_parameters.items()
            },
            "stability_window": dict(self.stability_window),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PhaseRecord":
        return cls(
            name=str(payload["name"]),
            fraction=float(payload["fraction"]),
            order=OrderClass(str(payload["order"])),
            space_group=payload.get("space_group"),
            lattice_parameters={
                str(name): Quantity.from_dict(value)
                for name, value in payload.get("lattice_parameters", {}).items()
            },
            stability_window=dict(payload.get("stability_window", {})),
            status=EpistemicStatus(
                payload.get("status", EpistemicStatus.MODEL_EXTRAPOLATION.value)
            ),
        )


@dataclass(frozen=True, slots=True)
class PropertyRecord:
    name: str
    domain: PropertyDomain
    quantity: Quantity
    direction: Sequence[float] | None = None
    tensor: Sequence[Sequence[float]] | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Property name cannot be empty")
        if self.direction is not None and len(self.direction) not in (2, 3):
            raise ValueError("Property direction must have two or three components")
        if self.tensor is not None:
            rows = [tuple(row) for row in self.tensor]
            if not rows or any(len(row) != len(rows) for row in rows):
                raise ValueError("Property tensor must be non-empty and square")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "domain": self.domain.value,
            "quantity": self.quantity.to_dict(),
            "direction": None if self.direction is None else list(self.direction),
            "tensor": None if self.tensor is None else [list(row) for row in self.tensor],
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "PropertyRecord":
        return cls(
            name=str(payload["name"]),
            domain=PropertyDomain(str(payload["domain"])),
            quantity=Quantity.from_dict(payload["quantity"]),
            direction=payload.get("direction"),
            tensor=payload.get("tensor"),
            note=payload.get("note"),
        )


def normalize_nonnegative_weights(values: Iterable[float]) -> tuple[float, ...]:
    items = tuple(float(value) for value in values)
    if not items:
        return ()
    if any(value < 0 for value in items):
        raise ValueError("Weights cannot be negative")
    total = sum(items)
    if total <= 0:
        return tuple(0.0 for _ in items)
    return tuple(value / total for value in items)
