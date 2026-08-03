from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping


class OakStatus(str, Enum):
    FERTILE = "fertile"
    DEFINED = "defined"
    CODED = "coded"
    TESTED = "tested"
    BENCHMARKED = "benchmarked"
    MEASURED = "measured"
    VALIDATED = "validated"


class CodeStatus(str, Enum):
    ABSENT = "absent"
    SKELETON = "skeleton"
    RUNNABLE = "runnable"
    TESTED = "tested"


class IpStatus(str, Enum):
    PUBLIC = "public"
    REVIEW_REQUIRED = "review_required"
    PATENT_CANDIDATE = "patent_candidate"
    TRADE_SECRET = "trade_secret"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    RESTRICTED = "restricted"


def _tuple_of_strings(value: Iterable[str] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(str(item) for item in value)


@dataclass(frozen=True, slots=True)
class NodeContract:
    """Machine-readable contract for one recursive creation node."""

    id: str
    name: str
    depth: int
    path: str
    parent_id: str | None
    root_creation: str
    role: str

    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    interfaces: tuple[str, ...] = ()

    scientific_basis: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    invariants: tuple[str, ...] = ()
    failure_modes: tuple[str, ...] = ()

    oak_status: OakStatus = OakStatus.FERTILE
    code_status: CodeStatus = CodeStatus.ABSENT
    ip_status: IpStatus = IpStatus.REVIEW_REQUIRED
    risk_level: RiskLevel = RiskLevel.LOW

    tests: tuple[str, ...] = ()
    baselines: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    m_plus: tuple[str, ...] = ()
    m_minus: tuple[str, ...] = ()

    product_path: tuple[str, ...] = ()
    next_proof: str = ""
    next_action_under_2h: str = ""
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or any(part == "" for part in self.id.split(".")):
            raise ValueError("node id must be a non-empty dotted identifier")
        if not self.name.strip():
            raise ValueError("node name cannot be empty")
        if self.depth < 0:
            raise ValueError("depth cannot be negative")
        if self.depth == 0 and self.parent_id is not None:
            raise ValueError("root node cannot have a parent")
        if self.depth > 0 and not self.parent_id:
            raise ValueError("non-root node requires parent_id")
        if not self.path:
            raise ValueError("path cannot be empty")
        if not self.root_creation:
            raise ValueError("root_creation cannot be empty")

    @property
    def is_root(self) -> bool:
        return self.depth == 0

    @property
    def is_atomic_candidate(self) -> bool:
        """A conservative local stop signal, not a permanent global depth cap."""
        return bool(
            self.interfaces
            and self.tests
            and self.next_proof.strip()
            and self.metadata.get("atomic", False)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "depth": self.depth,
            "path": self.path,
            "parent_id": self.parent_id,
            "root_creation": self.root_creation,
            "role": self.role,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "constraints": list(self.constraints),
            "dependencies": list(self.dependencies),
            "interfaces": list(self.interfaces),
            "scientific_basis": list(self.scientific_basis),
            "assumptions": list(self.assumptions),
            "invariants": list(self.invariants),
            "failure_modes": list(self.failure_modes),
            "oak_status": self.oak_status.value,
            "code_status": self.code_status.value,
            "ip_status": self.ip_status.value,
            "risk_level": self.risk_level.value,
            "tests": list(self.tests),
            "baselines": list(self.baselines),
            "evidence": list(self.evidence),
            "m_plus": list(self.m_plus),
            "m_minus": list(self.m_minus),
            "product_path": list(self.product_path),
            "next_proof": self.next_proof,
            "next_action_under_2h": self.next_action_under_2h,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "NodeContract":
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            depth=int(payload["depth"]),
            path=str(payload["path"]),
            parent_id=payload.get("parent_id"),
            root_creation=str(payload["root_creation"]),
            role=str(payload.get("role", "")),
            inputs=_tuple_of_strings(payload.get("inputs")),
            outputs=_tuple_of_strings(payload.get("outputs")),
            constraints=_tuple_of_strings(payload.get("constraints")),
            dependencies=_tuple_of_strings(payload.get("dependencies")),
            interfaces=_tuple_of_strings(payload.get("interfaces")),
            scientific_basis=_tuple_of_strings(payload.get("scientific_basis")),
            assumptions=_tuple_of_strings(payload.get("assumptions")),
            invariants=_tuple_of_strings(payload.get("invariants")),
            failure_modes=_tuple_of_strings(payload.get("failure_modes")),
            oak_status=OakStatus(payload.get("oak_status", OakStatus.FERTILE.value)),
            code_status=CodeStatus(payload.get("code_status", CodeStatus.ABSENT.value)),
            ip_status=IpStatus(payload.get("ip_status", IpStatus.REVIEW_REQUIRED.value)),
            risk_level=RiskLevel(payload.get("risk_level", RiskLevel.LOW.value)),
            tests=_tuple_of_strings(payload.get("tests")),
            baselines=_tuple_of_strings(payload.get("baselines")),
            evidence=_tuple_of_strings(payload.get("evidence")),
            m_plus=_tuple_of_strings(payload.get("m_plus")),
            m_minus=_tuple_of_strings(payload.get("m_minus")),
            product_path=_tuple_of_strings(payload.get("product_path")),
            next_proof=str(payload.get("next_proof", "")),
            next_action_under_2h=str(payload.get("next_action_under_2h", "")),
            tags=_tuple_of_strings(payload.get("tags")),
            metadata=dict(payload.get("metadata", {})),
        )
