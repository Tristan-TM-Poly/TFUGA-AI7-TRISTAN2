"""Typed graph intermediate representation for Ω-VLA-T∞³.

VLA-IR stores mathematical objects, relations, assumptions and provenance in a
canonical directed multigraph.  Validation here checks finite software
contracts; it is not a theorem prover.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable, Iterator, Mapping, Sequence

from .types import MathType, TypeSystemError, assert_unique_type_ids, math_type_from_dict


class IRError(ValueError):
    """Raised for malformed or inconsistent VLA-IR programs."""


class NodeKind(str, Enum):
    SYMBOL = "symbol"
    CONSTANT = "constant"
    SPACE = "space"
    SCALAR = "scalar"
    VECTOR = "vector"
    COVECTOR = "covector"
    MATRIX = "matrix"
    TENSOR = "tensor"
    OPERATOR = "operator"
    FIELD = "field"
    FORM = "differential_form"
    GRAPH = "graph"
    COMPLEX = "chain_complex"
    EQUATION = "equation"
    ASSUMPTION = "assumption"
    INVARIANT = "invariant"
    PROPOSITION = "proposition"
    PROOF_TARGET = "proof_target"
    TEST = "test"
    EXPERIMENT = "experiment"
    RESIDUAL = "residual"
    COUNTEREXAMPLE = "counterexample"
    ARTIFACT = "artifact"


class EdgeKind(str, Enum):
    BELONGS_TO = "belongs_to"
    DOMAIN_OF = "domain_of"
    CODOMAIN_OF = "codomain_of"
    ACTS_ON = "acts_on"
    OUTPUTS = "outputs"
    DEPENDS_ON = "depends_on"
    COMPOSES_WITH = "composes_with"
    DUAL_OF = "dual_of"
    ADJOINT_OF = "adjoint_of"
    INVARIANT_UNDER = "invariant_under"
    APPROXIMATES = "approximates"
    GENERALIZES = "generalizes"
    SPECIALIZES = "specializes"
    DISCRETIZES = "discretizes"
    PROVES = "proves"
    FALSIFIES = "falsifies"
    TESTS = "tests"
    PRODUCES = "produces"
    HAS_ASSUMPTION = "has_assumption"
    HAS_RESIDUAL = "has_residual"
    COMMUTES_WITH = "commutes_with"
    DOES_NOT_COMMUTE_WITH = "does_not_commute_with"
    EQUIVALENT_TO = "equivalent_to"
    REDUCES_TO = "reduces_to"


@dataclass(frozen=True)
class Provenance:
    source: str
    locator: str = ""
    method: str = "handwritten"
    confidence: float = 1.0
    license: str | None = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source.strip():
            raise IRError("provenance source cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise IRError("provenance confidence must lie in [0, 1]")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "locator": self.locator,
            "method": self.method,
            "confidence": self.confidence,
            "license": self.license,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class IRNode:
    node_id: str
    kind: NodeKind
    label: str
    math_type: MathType | None = None
    value: Any = None
    attributes: tuple[tuple[str, Any], ...] = ()
    provenance: Provenance | None = None

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise IRError("node_id cannot be empty")
        if not self.label.strip():
            raise IRError("node label cannot be empty")
        keys = [key for key, _ in self.attributes]
        if len(keys) != len(set(keys)):
            raise IRError(f"duplicate attribute key on node {self.node_id}")

    @classmethod
    def build(
        cls,
        node_id: str,
        kind: NodeKind,
        label: str,
        *,
        math_type: MathType | None = None,
        value: Any = None,
        attributes: Mapping[str, Any] | None = None,
        provenance: Provenance | None = None,
    ) -> "IRNode":
        return cls(
            node_id=node_id,
            kind=kind,
            label=label,
            math_type=math_type,
            value=value,
            attributes=tuple(sorted((attributes or {}).items())),
            provenance=provenance,
        )

    def attribute_map(self) -> dict[str, Any]:
        return dict(self.attributes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "kind": self.kind.value,
            "label": self.label,
            "math_type": None if self.math_type is None else self.math_type.to_dict(),
            "value": self.value,
            "attributes": self.attribute_map(),
            "provenance": None if self.provenance is None else self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class IREdge:
    source: str
    target: str
    kind: EdgeKind
    edge_id: str = ""
    attributes: tuple[tuple[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise IRError("edge endpoints cannot be empty")
        keys = [key for key, _ in self.attributes]
        if len(keys) != len(set(keys)):
            raise IRError("edge attributes must have unique keys")

    @classmethod
    def build(
        cls,
        source: str,
        target: str,
        kind: EdgeKind,
        *,
        edge_id: str = "",
        attributes: Mapping[str, Any] | None = None,
    ) -> "IREdge":
        return cls(
            source=source,
            target=target,
            kind=kind,
            edge_id=edge_id,
            attributes=tuple(sorted((attributes or {}).items())),
        )

    def stable_id(self) -> str:
        if self.edge_id:
            return self.edge_id
        payload = f"{self.source}|{self.kind.value}|{self.target}|{self.attributes}"
        return sha256(payload.encode("utf-8")).hexdigest()[:20]

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.stable_id(),
            "source": self.source,
            "target": self.target,
            "kind": self.kind.value,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class IRValidationIssue:
    code: str
    severity: str
    message: str
    subject: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "subject": self.subject,
        }


@dataclass(frozen=True)
class IRValidationReport:
    issues: tuple[IRValidationIssue, ...]

    @property
    def passed(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "issues": [issue.to_dict() for issue in self.issues],
            "theorem_claimed": False,
            "formal_proof_claimed": False,
            "scientific_validation_claimed": False,
        }


@dataclass
class VLAProgram:
    """Canonical mutable builder for an immutable serialized VLA-IR graph."""

    program_id: str
    title: str
    version: str = "0.3.0"
    nodes: dict[str, IRNode] = field(default_factory=dict)
    edges: list[IREdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.program_id.strip() or not self.title.strip():
            raise IRError("program id and title cannot be empty")

    def add_node(self, node: IRNode) -> IRNode:
        if node.node_id in self.nodes:
            raise IRError(f"duplicate node id: {node.node_id}")
        self.nodes[node.node_id] = node
        return node

    def replace_node(self, node: IRNode) -> IRNode:
        if node.node_id not in self.nodes:
            raise IRError(f"cannot replace unknown node: {node.node_id}")
        self.nodes[node.node_id] = node
        return node

    def add_edge(self, edge: IREdge) -> IREdge:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise IRError(
                f"edge endpoints must exist before insertion: {edge.source} -> {edge.target}"
            )
        stable = edge.stable_id()
        if any(existing.stable_id() == stable for existing in self.edges):
            raise IRError(f"duplicate edge id: {stable}")
        self.edges.append(edge)
        return edge

    def node(self, node_id: str) -> IRNode:
        try:
            return self.nodes[node_id]
        except KeyError as exc:
            raise IRError(f"unknown node id: {node_id}") from exc

    def outgoing(self, node_id: str, kind: EdgeKind | None = None) -> tuple[IREdge, ...]:
        return tuple(
            edge
            for edge in self.edges
            if edge.source == node_id and (kind is None or edge.kind == kind)
        )

    def incoming(self, node_id: str, kind: EdgeKind | None = None) -> tuple[IREdge, ...]:
        return tuple(
            edge
            for edge in self.edges
            if edge.target == node_id and (kind is None or edge.kind == kind)
        )

    def neighbors(self, node_id: str) -> tuple[str, ...]:
        result = {
            edge.target for edge in self.outgoing(node_id)
        } | {
            edge.source for edge in self.incoming(node_id)
        }
        return tuple(sorted(result))

    def dependency_order(self) -> tuple[str, ...]:
        """Topological order over DEPENDS_ON edges.

        An edge A DEPENDS_ON B means B must precede A.
        """

        indegree = {node_id: 0 for node_id in self.nodes}
        forward: dict[str, list[str]] = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            if edge.kind != EdgeKind.DEPENDS_ON:
                continue
            indegree[edge.source] += 1
            forward[edge.target].append(edge.source)
        queue = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
        result: list[str] = []
        while queue:
            current = queue.pop(0)
            result.append(current)
            for dependent in sorted(forward[current]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    queue.append(dependent)
                    queue.sort()
        if len(result) != len(self.nodes):
            cyclic = sorted(node_id for node_id, degree in indegree.items() if degree > 0)
            raise IRError(f"dependency cycle detected: {', '.join(cyclic)}")
        return tuple(result)

    def validate(self) -> IRValidationReport:
        issues: list[IRValidationIssue] = []
        try:
            assert_unique_type_ids(
                (node.node_id, node.math_type)
                for node in self.nodes.values()
                if node.math_type is not None
            )
        except TypeSystemError as exc:
            issues.append(IRValidationIssue("TYPE_ID", "error", str(exc)))

        edge_ids: set[str] = set()
        for edge in self.edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                issues.append(
                    IRValidationIssue(
                        "DANGLING_EDGE",
                        "error",
                        "edge endpoint is missing",
                        edge.stable_id(),
                    )
                )
            if edge.stable_id() in edge_ids:
                issues.append(
                    IRValidationIssue(
                        "DUPLICATE_EDGE",
                        "error",
                        "duplicate edge identifier",
                        edge.stable_id(),
                    )
                )
            edge_ids.add(edge.stable_id())

        for node in self.nodes.values():
            if node.kind in {NodeKind.VECTOR, NodeKind.COVECTOR, NodeKind.MATRIX, NodeKind.OPERATOR} and node.math_type is None:
                issues.append(
                    IRValidationIssue(
                        "UNTYPED_MATH_NODE",
                        "error",
                        "mathematical node requires a MathType",
                        node.node_id,
                    )
                )
            if node.provenance is None:
                issues.append(
                    IRValidationIssue(
                        "MISSING_PROVENANCE",
                        "warning",
                        "node has no provenance record",
                        node.node_id,
                    )
                )

        for edge in self.edges:
            source = self.nodes.get(edge.source)
            target = self.nodes.get(edge.target)
            if source is None or target is None:
                continue
            if edge.kind == EdgeKind.ADJOINT_OF:
                if source.math_type is None or target.math_type is None:
                    issues.append(IRValidationIssue("ADJOINT_TYPE", "error", "adjoint relation requires typed nodes", edge.stable_id()))
                else:
                    try:
                        expected = target.math_type.adjoint_result()
                        if source.math_type != expected:
                            issues.append(IRValidationIssue("ADJOINT_MISMATCH", "error", "adjoint relation type mismatch", edge.stable_id()))
                    except TypeSystemError as exc:
                        issues.append(IRValidationIssue("ADJOINT_INVALID", "error", str(exc), edge.stable_id()))
            if edge.kind in {EdgeKind.COMMUTES_WITH, EdgeKind.DOES_NOT_COMMUTE_WITH}:
                if source.math_type is None or target.math_type is None:
                    issues.append(IRValidationIssue("COMMUTATOR_TYPE", "error", "commutator relation requires typed operators", edge.stable_id()))
                elif source.math_type != target.math_type:
                    issues.append(IRValidationIssue("COMMUTATOR_MISMATCH", "error", "commutator operands must share a type", edge.stable_id()))

        try:
            self.dependency_order()
        except IRError as exc:
            issues.append(IRValidationIssue("DEPENDENCY_CYCLE", "error", str(exc)))

        return IRValidationReport(tuple(issues))

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": "omega-vla-ir-v1",
            "program_id": self.program_id,
            "title": self.title,
            "version": self.version,
            "nodes": [self.nodes[node_id].to_dict() for node_id in sorted(self.nodes)],
            "edges": [
                edge.to_dict()
                for edge in sorted(
                    self.edges,
                    key=lambda value: (value.source, value.kind.value, value.target, value.stable_id()),
                )
            ],
            "metadata": self.metadata,
            "claim_boundaries": {
                "theorem_claimed": False,
                "formal_proof_claimed": False,
                "scientific_validation_claimed": False,
            },
        }

    def canonical_json(self, *, indent: int | None = None) -> str:
        return json.dumps(
            self.canonical_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":") if indent is None else None,
            indent=indent,
        )

    def digest(self) -> str:
        return sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def clone(self, *, program_id: str | None = None, title: str | None = None) -> "VLAProgram":
        return VLAProgram.from_dict(
            {
                **self.canonical_payload(),
                "program_id": program_id or self.program_id,
                "title": title or self.title,
            }
        )

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "VLAProgram":
        program = cls(
            program_id=str(payload["program_id"]),
            title=str(payload["title"]),
            version=str(payload.get("version", "0.3.0")),
            metadata=dict(payload.get("metadata", {})),
        )
        for raw in payload.get("nodes", []):
            provenance_payload = raw.get("provenance")
            provenance = None
            if provenance_payload is not None:
                provenance = Provenance(
                    source=str(provenance_payload["source"]),
                    locator=str(provenance_payload.get("locator", "")),
                    method=str(provenance_payload.get("method", "handwritten")),
                    confidence=float(provenance_payload.get("confidence", 1.0)),
                    license=provenance_payload.get("license"),
                    notes=tuple(str(note) for note in provenance_payload.get("notes", [])),
                )
            node = IRNode.build(
                str(raw["node_id"]),
                NodeKind(raw["kind"]),
                str(raw["label"]),
                math_type=None if raw.get("math_type") is None else math_type_from_dict(raw["math_type"]),
                value=raw.get("value"),
                attributes=raw.get("attributes", {}),
                provenance=provenance,
            )
            program.add_node(node)
        for raw in payload.get("edges", []):
            program.add_edge(
                IREdge.build(
                    str(raw["source"]),
                    str(raw["target"]),
                    EdgeKind(raw["kind"]),
                    edge_id=str(raw.get("edge_id", "")),
                    attributes=raw.get("attributes", {}),
                )
            )
        return program

    @classmethod
    def from_json(cls, text: str) -> "VLAProgram":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise IRError("VLA-IR JSON root must be an object")
        return cls.from_dict(payload)


def merge_programs(
    programs: Sequence[VLAProgram],
    *,
    program_id: str,
    title: str,
    namespace_nodes: bool = True,
) -> VLAProgram:
    """Merge programs while preserving provenance and preventing collisions."""

    merged = VLAProgram(program_id=program_id, title=title)
    for program in programs:
        mapping: dict[str, str] = {}
        for node_id, node in program.nodes.items():
            target_id = f"{program.program_id}:{node_id}" if namespace_nodes else node_id
            mapping[node_id] = target_id
            merged.add_node(
                IRNode(
                    node_id=target_id,
                    kind=node.kind,
                    label=node.label,
                    math_type=node.math_type,
                    value=node.value,
                    attributes=node.attributes,
                    provenance=node.provenance,
                )
            )
        for edge in program.edges:
            merged.add_edge(
                IREdge(
                    source=mapping[edge.source],
                    target=mapping[edge.target],
                    kind=edge.kind,
                    edge_id=f"{program.program_id}:{edge.stable_id()}",
                    attributes=edge.attributes,
                )
            )
    merged.metadata["merged_programs"] = [program.program_id for program in programs]
    return merged
