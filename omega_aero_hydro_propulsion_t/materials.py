from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .structural import BladeMaterial


@dataclass(frozen=True)
class MaterialRecord:
    material: BladeMaterial
    source_type: str
    provenance: str
    manufacturing_notes: tuple[str, ...] = ()
    engineering_allowables: bool = False

    def validate(self) -> None:
        self.material.validate()
        if not self.source_type.strip() or not self.provenance.strip():
            raise ValueError("material source_type and provenance are required")
        if any(not note.strip() for note in self.manufacturing_notes):
            raise ValueError("manufacturing notes cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "material": self.material.to_dict(),
            "source_type": self.source_type,
            "provenance": self.provenance,
            "manufacturing_notes": list(self.manufacturing_notes),
            "engineering_allowables": self.engineering_allowables,
        }


class MaterialAtlas:
    def __init__(self, records: Iterable[MaterialRecord] = ()) -> None:
        self._records: dict[str, MaterialRecord] = {}
        for record in records:
            self.register(record)

    def register(self, record: MaterialRecord, *, replace: bool = False) -> None:
        record.validate()
        key = record.material.name
        if key in self._records and not replace:
            raise ValueError(f"material already registered: {key}")
        self._records[key] = record

    def contains(self, name: str) -> bool:
        return name in self._records

    def get_record(self, name: str) -> MaterialRecord:
        try:
            return self._records[name]
        except KeyError as exc:
            raise KeyError(f"unknown material: {name}") from exc

    def get(self, name: str) -> BladeMaterial:
        return self.get_record(name).material

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._records))

    def to_dict(self) -> dict[str, Any]:
        return {"records": [self._records[name].to_dict() for name in self.names]}


def default_material_atlas() -> MaterialAtlas:
    fixture_notice = "generic deterministic screening fixture; replace with traceable coupon and laminate allowables"
    return MaterialAtlas(
        (
            MaterialRecord(
                BladeMaterial("generic-carbon-epoxy-screening", 1600.0, 70.0e9, 450.0e6, 220.0e6),
                "synthetic-screening",
                fixture_notice,
                ("anisotropy and laminate schedule are not resolved",),
            ),
            MaterialRecord(
                BladeMaterial("generic-glass-epoxy-screening", 1900.0, 40.0e9, 250.0e6, 120.0e6),
                "synthetic-screening",
                fixture_notice,
                ("anisotropy and moisture effects are not resolved",),
            ),
            MaterialRecord(
                BladeMaterial("generic-aluminum-screening", 2700.0, 69.0e9, 250.0e6, 95.0e6),
                "synthetic-screening",
                fixture_notice,
                ("alloy, temper, joints and corrosion are not resolved",),
            ),
            MaterialRecord(
                BladeMaterial("generic-titanium-screening", 4430.0, 114.0e9, 700.0e6, 330.0e6),
                "synthetic-screening",
                fixture_notice,
                ("alloy, forging route and notch effects are not resolved",),
            ),
            MaterialRecord(
                BladeMaterial("generic-laminated-wood-screening", 650.0, 12.0e9, 45.0e6, 20.0e6),
                "synthetic-screening",
                fixture_notice,
                ("grain, humidity, adhesive and defect statistics are not resolved",),
            ),
        )
    )
