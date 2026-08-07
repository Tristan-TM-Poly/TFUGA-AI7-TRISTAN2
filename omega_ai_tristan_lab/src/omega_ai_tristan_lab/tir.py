"""Tristan Intermediate Representation (TIR)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from hashlib import sha256
import json
from typing import Any, Mapping


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def stable_digest(value: Any) -> str:
    encoded = json.dumps(
        _jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class Provenance:
    source: str
    version: str = ""
    operation: str = ""
    parents: tuple[str, ...] = ()
    commit: str = ""
    distribution: str = ""
    repository: str = ""
    install_source: str = ""
    wheel_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Uncertainty:
    numerical: float | None = None
    model: float | None = None
    data: float | None = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TristanArtifact:
    id: str
    kind: str
    payload: Any
    provenance: Provenance
    uncertainty: Uncertainty = field(default_factory=Uncertainty)
    oak_status: str = "UNVERIFIED"
    schema_version: str = "tir-0.2"
    digest: str = ""

    @classmethod
    def build(
        cls,
        *,
        kind: str,
        payload: Any,
        provenance: Provenance,
        uncertainty: Uncertainty | None = None,
        oak_status: str = "UNVERIFIED",
        schema_version: str = "tir-0.2",
    ) -> "TristanArtifact":
        uncertainty_value = uncertainty or Uncertainty()
        digest = stable_digest(
            {
                "kind": kind,
                "payload": payload,
                "provenance": provenance,
                "uncertainty": uncertainty_value,
                "oak_status": oak_status,
                "schema_version": schema_version,
            }
        )
        return cls(
            id=f"tir:{digest[:20]}",
            kind=kind,
            payload=payload,
            provenance=provenance,
            uncertainty=uncertainty_value,
            oak_status=oak_status,
            schema_version=schema_version,
            digest=digest,
        )

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))
