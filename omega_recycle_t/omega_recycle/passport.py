from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from .models import Component


@dataclass(frozen=True, slots=True)
class MaterialPassport:
    product_id: str
    schema_version: str
    components: tuple[Component, ...]
    provenance: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {"product_id": self.product_id, "schema_version": self.schema_version, "provenance": self.provenance, "notes": list(self.notes), "components": [asdict(component) for component in self.components]}

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, payload: dict) -> "MaterialPassport":
        return cls(product_id=payload["product_id"], schema_version=payload["schema_version"], provenance=payload["provenance"], notes=tuple(payload.get("notes", [])), components=tuple(Component(**item) for item in payload["components"]))

    @classmethod
    def from_json(cls, payload: str) -> "MaterialPassport":
        return cls.from_dict(json.loads(payload))
