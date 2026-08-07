"""Schema contracts and compatibility graph for Tristan capabilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SchemaSpec:
    id: str
    kind: str = "mapping"
    required_keys: tuple[str, ...] = ()
    optional_keys: tuple[str, ...] = ()
    allow_extra: bool = True
    description: str = ""

    def validate(self, payload: Any) -> tuple[str, ...]:
        errors: list[str] = []
        if self.kind == "mapping":
            if not isinstance(payload, Mapping):
                return (f"expected mapping for schema {self.id!r}",)
            keys = {str(key) for key in payload}
            missing = [key for key in self.required_keys if key not in keys]
            if missing:
                errors.append(f"missing required keys: {', '.join(sorted(missing))}")
            if not self.allow_extra:
                allowed = set(self.required_keys) | set(self.optional_keys)
                extra = sorted(keys - allowed)
                if extra:
                    errors.append(f"unexpected keys: {', '.join(extra)}")
        return tuple(errors)

    def compatible_with(self, downstream: "SchemaSpec") -> bool:
        if self.id == downstream.id:
            return True
        if self.id == "tristan.any" or downstream.id == "tristan.any":
            return True
        if self.kind != downstream.kind:
            return False
        if self.kind != "mapping":
            return False
        produced = set(self.required_keys) | set(self.optional_keys)
        return set(downstream.required_keys).issubset(produced) and (
            downstream.allow_extra or produced.issubset(set(downstream.required_keys) | set(downstream.optional_keys))
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SchemaGraph:
    """Registry + compatibility relation for TIR payload schemas."""

    def __init__(self) -> None:
        self._schemas: dict[str, SchemaSpec] = {
            "tristan.any": SchemaSpec("tristan.any", kind="any", description="Wildcard legacy schema."),
            "tristan.mapping": SchemaSpec("tristan.mapping", kind="mapping", description="Generic mapping."),
        }

    def register(self, schema: SchemaSpec, *, replace: bool = False) -> None:
        if schema.id in self._schemas and not replace:
            if self._schemas[schema.id] != schema:
                raise ValueError(f"Schema already registered with different contract: {schema.id}")
            return
        self._schemas[schema.id] = schema

    def get(self, schema_id: str) -> SchemaSpec:
        if not schema_id:
            return self._schemas["tristan.any"]
        if schema_id not in self._schemas:
            raise KeyError(f"Unknown schema: {schema_id}")
        return self._schemas[schema_id]

    def validate(self, schema_id: str, payload: Any) -> tuple[str, ...]:
        return self.get(schema_id).validate(payload)

    def compatible(self, upstream_id: str, downstream_id: str) -> bool:
        return self.get(upstream_id).compatible_with(self.get(downstream_id))

    def to_dict(self) -> dict[str, Any]:
        ids = sorted(self._schemas)
        return {
            "schemas": {schema_id: self._schemas[schema_id].to_dict() for schema_id in ids},
            "compatible_edges": [
                {"from": source, "to": target}
                for source in ids
                for target in ids
                if self.compatible(source, target)
            ],
        }


def coerce_schema_spec(raw: Any) -> SchemaSpec:
    """Normalize central or peer-declared schemas without import coupling."""
    if isinstance(raw, SchemaSpec):
        return raw
    if isinstance(raw, Mapping):
        data = dict(raw)
    elif callable(getattr(raw, "to_dict", None)):
        data = dict(raw.to_dict())
    else:
        names = ("id", "kind", "required_keys", "optional_keys", "allow_extra", "description")
        data = {name: getattr(raw, name) for name in names if hasattr(raw, name)}
    for key in ("required_keys", "optional_keys"):
        if key in data:
            data[key] = tuple(str(item) for item in data[key])
    if "id" not in data:
        raise TypeError("schema spec must declare id")
    return SchemaSpec(**data)


def specs_from_plugin(plugin: Any) -> tuple[SchemaSpec, ...]:
    rich = getattr(plugin, "schema_specs", None)
    if not callable(rich):
        return ()
    return tuple(coerce_schema_spec(item) for item in rich())
