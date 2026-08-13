from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Mapping, Sequence
import json

SCHEMA_VERSION = "0.1.0"
GRAPH_KINDS = ("knowledge", "capability", "work", "experiment", "provenance", "value")
AUTHORITIES = ("read", "draft", "write", "irreversible")
OAK_STATES = ("UNKNOWN", "HOLD", "PASS", "FAIL")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_digest(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ObjectRef:
    graph: str
    object_type: str
    object_id: str
    content_hash: str = ""
    version: str = ""

    def __post_init__(self) -> None:
        if self.graph not in GRAPH_KINDS:
            raise ValueError(f"unknown graph kind: {self.graph}")
        if not self.object_type or not self.object_id:
            raise ValueError("object_type and object_id are required")

    @property
    def key(self) -> str:
        return f"{self.graph}:{self.object_type}:{self.object_id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Envelope:
    graph: str
    object_type: str
    object_id: str
    payload: Mapping[str, Any]
    provenance: tuple[str, ...] = ()
    uncertainty: float = 0.0
    authority: str = "read"
    oak_state: str = "UNKNOWN"
    valid_time: str | None = None
    known_time: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.graph not in GRAPH_KINDS:
            raise ValueError(f"unknown graph kind: {self.graph}")
        if self.authority not in AUTHORITIES:
            raise ValueError(f"invalid authority: {self.authority}")
        if self.oak_state not in OAK_STATES:
            raise ValueError(f"invalid OAK state: {self.oak_state}")
        if not 0.0 <= float(self.uncertainty) <= 1.0:
            raise ValueError("uncertainty must be in [0,1]")
        if not self.object_type or not self.object_id:
            raise ValueError("object_type and object_id are required")

    @property
    def content_hash(self) -> str:
        return stable_digest(dict(self.payload))

    @property
    def ref(self) -> ObjectRef:
        return ObjectRef(
            graph=self.graph,
            object_type=self.object_type,
            object_id=self.object_id,
            content_hash=self.content_hash,
            version=self.schema_version,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "graph": self.graph,
            "object_type": self.object_type,
            "object_id": self.object_id,
            "content_hash": self.content_hash,
            "payload": dict(self.payload),
            "provenance": list(self.provenance),
            "uncertainty": self.uncertainty,
            "authority": self.authority,
            "oak_state": self.oak_state,
            "valid_time": self.valid_time,
            "known_time": self.known_time,
        }


@dataclass(frozen=True)
class GraphEdge:
    source: ObjectRef
    target: ObjectRef
    relation: str
    evidence_refs: tuple[ObjectRef, ...] = ()
    causal_claim: bool = False
    uncertainty: float = 0.0

    def __post_init__(self) -> None:
        if not self.relation:
            raise ValueError("relation is required")
        if not 0.0 <= float(self.uncertainty) <= 1.0:
            raise ValueError("edge uncertainty must be in [0,1]")
        if self.causal_claim and not self.evidence_refs:
            raise ValueError("causal_claim requires explicit evidence_refs")

    @property
    def fingerprint(self) -> str:
        return stable_digest({
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "relation": self.relation,
            "evidence_refs": [item.to_dict() for item in self.evidence_refs],
            "causal_claim": self.causal_claim,
            "uncertainty": self.uncertainty,
        })


@dataclass(frozen=True)
class InvariantCheck:
    name: str
    status: str
    detail: str = ""

    def __post_init__(self) -> None:
        if self.status not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError(f"invalid invariant status: {self.status}")


@dataclass(frozen=True)
class TransformationReceipt:
    receipt_id: str
    operator: str
    inputs: tuple[ObjectRef, ...]
    outputs: tuple[ObjectRef, ...]
    assumptions: tuple[str, ...] = ()
    invariants: tuple[InvariantCheck, ...] = ()
    evidence_refs: tuple[ObjectRef, ...] = ()
    residuals: tuple[str, ...] = ()
    uncertainty: float = 0.0
    cost: float = 0.0
    authority: str = "read"
    risk: float = 0.0
    rollback: str = ""
    provenance: tuple[str, ...] = ()
    oak_state: str = "UNKNOWN"
    schema_version: str = SCHEMA_VERSION

    @property
    def fingerprint(self) -> str:
        payload = asdict(self)
        payload.pop("receipt_id", None)
        return stable_digest(payload)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["fingerprint"] = self.fingerprint
        return payload
