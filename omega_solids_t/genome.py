from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import (
    BondContribution,
    CompositionComponent,
    DefectRecord,
    Dimensionality,
    EpistemicStatus,
    InterfaceRecord,
    OrderClass,
    PhaseRecord,
    PropertyRecord,
)


@dataclass(frozen=True, slots=True)
class SolidGenome:
    """Canonical, serializable description of a solid and its history.

    A genome is deliberately richer than a chemical formula: it includes
    structure, interfaces, defects, processing, evidence, uncertainty and
    next experiments. The same composition can therefore map to several
    materially distinct genomes.
    """

    identifier: str
    name: str
    family: str
    composition: tuple[CompositionComponent, ...]
    bonds: tuple[BondContribution, ...]
    order: OrderClass
    dimensionality: Dimensionality = Dimensionality.THREE_D
    phases: tuple[PhaseRecord, ...] = ()
    defects: tuple[DefectRecord, ...] = ()
    interfaces: tuple[InterfaceRecord, ...] = ()
    properties: tuple[PropertyRecord, ...] = ()
    geometry: Mapping[str, Any] = field(default_factory=dict)
    process: tuple[Mapping[str, Any], ...] = ()
    history: tuple[Mapping[str, Any], ...] = ()
    fields: Mapping[str, Any] = field(default_factory=dict)
    environment: Mapping[str, Any] = field(default_factory=dict)
    applications: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    provenance: tuple[Mapping[str, Any], ...] = ()
    assumptions: tuple[str, ...] = ()
    next_experiments: tuple[str, ...] = ()
    status: EpistemicStatus = EpistemicStatus.MODEL_EXTRAPOLATION
    schema_version: str = "0.1.0"
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("SolidGenome.identifier cannot be empty")
        if not self.name.strip():
            raise ValueError("SolidGenome.name cannot be empty")
        if not self.family.strip():
            raise ValueError("SolidGenome.family cannot be empty")
        if not self.composition:
            raise ValueError("SolidGenome.composition cannot be empty")
        if any(not application.strip() for application in self.applications):
            raise ValueError("Applications cannot contain empty values")
        self._validate_fraction_group(
            (component.fraction for component in self.composition),
            "composition",
            tolerance=5e-3,
        )
        if self.phases:
            self._validate_fraction_group(
                (phase.fraction for phase in self.phases),
                "phase",
                tolerance=5e-3,
            )
        if self.bonds:
            total = sum(bond.weight for bond in self.bonds)
            if not 0.995 <= total <= 1.005:
                raise ValueError(f"Bond weights must sum to one; got {total:.6g}")
        property_names = [record.name for record in self.properties]
        if len(property_names) != len(set(property_names)):
            raise ValueError("Property names must be unique within one genome")

    @staticmethod
    def _validate_fraction_group(
        values: Iterable[float], label: str, *, tolerance: float
    ) -> None:
        total = sum(values)
        if abs(total - 1.0) > tolerance:
            raise ValueError(f"{label.title()} fractions must sum to one; got {total:.6g}")

    @property
    def formula(self) -> str:
        parts: list[str] = []
        for component in self.composition:
            fraction = component.fraction
            if abs(fraction - round(fraction)) < 1e-12:
                suffix = "" if round(fraction) == 1 else str(round(fraction))
            else:
                suffix = f"{fraction:.4g}"
            parts.append(f"{component.species}{suffix}")
        return "".join(parts)

    def property_map(self) -> dict[str, PropertyRecord]:
        return {record.name: record for record in self.properties}

    def with_property(self, record: PropertyRecord) -> "SolidGenome":
        current = self.property_map()
        current[record.name] = record
        return replace(self, properties=tuple(current[name] for name in sorted(current)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "identifier": self.identifier,
            "name": self.name,
            "family": self.family,
            "composition": [component.to_dict() for component in self.composition],
            "bonds": [bond.to_dict() for bond in self.bonds],
            "order": self.order.value,
            "dimensionality": self.dimensionality.value,
            "phases": [phase.to_dict() for phase in self.phases],
            "defects": [defect.to_dict() for defect in self.defects],
            "interfaces": [interface.to_dict() for interface in self.interfaces],
            "properties": [record.to_dict() for record in self.properties],
            "geometry": dict(self.geometry),
            "process": [dict(step) for step in self.process],
            "history": [dict(event) for event in self.history],
            "fields": dict(self.fields),
            "environment": dict(self.environment),
            "applications": list(self.applications),
            "risks": list(self.risks),
            "provenance": [dict(record) for record in self.provenance],
            "assumptions": list(self.assumptions),
            "next_experiments": list(self.next_experiments),
            "status": self.status.value,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SolidGenome":
        return cls(
            identifier=str(payload["identifier"]),
            name=str(payload["name"]),
            family=str(payload["family"]),
            composition=tuple(
                CompositionComponent.from_dict(item)
                for item in payload.get("composition", [])
            ),
            bonds=tuple(
                BondContribution.from_dict(item) for item in payload.get("bonds", [])
            ),
            order=OrderClass(str(payload.get("order", OrderClass.UNKNOWN.value))),
            dimensionality=Dimensionality(
                str(payload.get("dimensionality", Dimensionality.THREE_D.value))
            ),
            phases=tuple(
                PhaseRecord.from_dict(item) for item in payload.get("phases", [])
            ),
            defects=tuple(
                DefectRecord.from_dict(item) for item in payload.get("defects", [])
            ),
            interfaces=tuple(
                InterfaceRecord.from_dict(item)
                for item in payload.get("interfaces", [])
            ),
            properties=tuple(
                PropertyRecord.from_dict(item)
                for item in payload.get("properties", [])
            ),
            geometry=dict(payload.get("geometry", {})),
            process=tuple(dict(item) for item in payload.get("process", [])),
            history=tuple(dict(item) for item in payload.get("history", [])),
            fields=dict(payload.get("fields", {})),
            environment=dict(payload.get("environment", {})),
            applications=tuple(str(item) for item in payload.get("applications", [])),
            risks=tuple(str(item) for item in payload.get("risks", [])),
            provenance=tuple(dict(item) for item in payload.get("provenance", [])),
            assumptions=tuple(str(item) for item in payload.get("assumptions", [])),
            next_experiments=tuple(
                str(item) for item in payload.get("next_experiments", [])
            ),
            status=EpistemicStatus(
                str(
                    payload.get(
                        "status", EpistemicStatus.MODEL_EXTRAPOLATION.value
                    )
                )
            ),
            schema_version=str(payload.get("schema_version", "0.1.0")),
            created_at=str(
                payload.get("created_at", datetime.now(timezone.utc).isoformat())
            ),
        )

    def canonical_json(self) -> str:
        payload = self.to_dict()
        payload.pop("created_at", None)

        def normalize(value: Any) -> Any:
            if isinstance(value, bool) or value is None or isinstance(value, str):
                return value
            if isinstance(value, (int, float)):
                number = float(value)
                if not number == number or number in (float("inf"), float("-inf")):
                    raise ValueError("Genome fingerprint cannot contain non-finite numbers")
                return number
            if isinstance(value, Mapping):
                return {str(key): normalize(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [normalize(item) for item in value]
            raise TypeError(f"Unsupported canonical genome value: {type(value).__name__}")

        return json.dumps(
            normalize(payload),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def load_genome(path: str | Path) -> SolidGenome:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("Solid genome JSON root must be an object")
    return SolidGenome.from_dict(payload)


def save_genome(genome: SolidGenome, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(genome.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return target
