"""Typed records for repaired tensor products and OAK evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping

from .linalg import Matrix, Vector, frobenius_norm


def canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class TensorChannel:
    name: str
    dimension: int
    values: Vector
    symmetry: str
    parent: str | None = None
    exact: bool = True
    interpretation: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.dimension < 0:
            raise ValueError("channel dimension must be non-negative")
        if len(self.values) != self.dimension:
            raise ValueError("channel dimension must match value count")

    @property
    def energy(self) -> float:
        return sum(value * value for value in self.values)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "dimension": self.dimension,
            "values": list(self.values),
            "symmetry": self.symmetry,
            "parent": self.parent,
            "exact": self.exact,
            "interpretation": self.interpretation,
            "metadata": dict(self.metadata),
            "energy": self.energy,
        }


@dataclass(frozen=True)
class RepairBundle:
    input_left: Vector
    input_right: Vector
    full_tensor: Matrix
    channels: tuple[TensorChannel, ...]
    reconstruction: Matrix
    residual: Matrix
    status: str
    claims: Mapping[str, bool] = field(default_factory=dict)

    @property
    def input_dimensions(self) -> tuple[int, int]:
        return len(self.input_left), len(self.input_right)

    @property
    def full_dimension(self) -> int:
        rows = len(self.full_tensor)
        cols = len(self.full_tensor[0]) if rows else 0
        return rows * cols

    @property
    def residual_norm(self) -> float:
        return frobenius_norm(self.residual)

    def channel(self, name: str) -> TensorChannel:
        for channel in self.channels:
            if channel.name == name:
                return channel
        raise KeyError(name)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "input_left": list(self.input_left),
            "input_right": list(self.input_right),
            "input_dimensions": list(self.input_dimensions),
            "full_tensor": [list(row) for row in self.full_tensor],
            "full_dimension": self.full_dimension,
            "channels": [channel.to_dict() for channel in self.channels],
            "reconstruction": [list(row) for row in self.reconstruction],
            "residual": [list(row) for row in self.residual],
            "residual_norm": self.residual_norm,
            "status": self.status,
            "claims": dict(self.claims),
        }
        payload["sha256"] = sha256(canonical_json(payload).encode("utf-8")).hexdigest()
        return payload


@dataclass(frozen=True)
class BranchNode:
    node_id: str
    dimension: int
    symmetry: str
    parent_id: str | None
    children_ids: tuple[str, ...] = tuple()
    exact_partition: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SymmetryTower:
    name: str
    nodes: tuple[BranchNode, ...]

    def node(self, node_id: str) -> BranchNode:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        raise KeyError(node_id)

    def roots(self) -> tuple[BranchNode, ...]:
        return tuple(node for node in self.nodes if node.parent_id is None)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "nodes": [node.to_dict() for node in self.nodes]}


@dataclass(frozen=True)
class AuditCheck:
    name: str
    passed: bool
    observed: float | int | str | bool
    expected: float | int | str | bool
    tolerance: float | None = None
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OAKReport:
    status: str
    checks: tuple[AuditCheck, ...]
    metrics: Mapping[str, float | int | str | bool]
    boundaries: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "status": self.status,
            "passed": self.passed,
            "checks": [check.to_dict() for check in self.checks],
            "metrics": dict(self.metrics),
            "boundaries": list(self.boundaries),
        }
        payload["sha256"] = sha256(canonical_json(payload).encode("utf-8")).hexdigest()
        return payload
