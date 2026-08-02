"""Universal intermediate representation for reverse-engineering evidence.

RE-IR is a provenance-first directed hypergraph. It can encode systems at
multiple resolutions without promoting an inference into an observation.
"""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
from json import dumps, loads
from typing import Any, Callable, Iterable, Mapping


class NodeKind(str, Enum):
    ENTITY = "entity"
    COMPONENT = "component"
    PORT = "port"
    CHANNEL = "channel"
    STATE = "state"
    VARIABLE = "variable"
    EVENT = "event"
    CONSTRAINT = "constraint"
    INVARIANT = "invariant"
    RESOURCE = "resource"
    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"
    EXPERIMENT = "experiment"
    CLAIM = "claim"
    EVIDENCE = "evidence"
    RESIDUAL = "residual"
    VERSION = "version"
    RISK = "risk"
    PERMISSION = "permission"
    ARTIFACT = "artifact"


class EdgeKind(str, Enum):
    CONTAINS = "contains"
    CONNECTS = "connects"
    CAUSES = "causes"
    PRECEDES = "precedes"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DERIVED_FROM = "derived_from"
    OBSERVED_BY = "observed_by"
    CONSTRAINS = "constrains"
    TRANSFORMS = "transforms"
    EQUIVALENT_TO = "equivalent_to"
    VERSION_OF = "version_of"
    AUTHORIZES = "authorizes"
    VALID_WITHIN = "valid_within"
    GENERATES = "generates"
    EXPLAINS = "explains"


class EpistemicLevel(str, Enum):
    OBSERVED = "observed"
    MEASURED = "measured"
    DERIVED = "derived"
    INFERRED = "inferred"
    PLAUSIBLE = "plausible"
    RECONSTRUCTED = "reconstructed"
    CAUSALLY_SUPPORTED = "causally_supported"
    INDEPENDENTLY_REPLICATED = "independently_replicated"
    VERIFIED_WITHIN_DOMAIN = "verified_within_domain"
    FALSIFIED = "falsified"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class IRNode:
    node_id: str
    kind: NodeKind
    label: str
    level: EpistemicLevel = EpistemicLevel.UNKNOWN
    attributes: Mapping[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()
    uncertainty: float = 1.0

    def __post_init__(self) -> None:
        if not self.node_id.strip() or not self.label.strip():
            raise ValueError("node_id and label are required")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be in [0, 1]")
        if (
            self.level
            in {
                EpistemicLevel.OBSERVED,
                EpistemicLevel.MEASURED,
                EpistemicLevel.VERIFIED_WITHIN_DOMAIN,
            }
            and not self.provenance
        ):
            raise ValueError(
                f"{self.level.value} nodes require provenance"
            )


@dataclass(frozen=True, slots=True)
class IREdge:
    edge_id: str
    source: str
    target: str
    kind: EdgeKind
    attributes: Mapping[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()
    confidence: float = 0.5

    def __post_init__(self) -> None:
        if (
            not self.edge_id.strip()
            or not self.source.strip()
            or not self.target.strip()
        ):
            raise ValueError("edge_id, source and target are required")
        if self.source == self.target and self.kind not in {
            EdgeKind.EQUIVALENT_TO,
            EdgeKind.VERSION_OF,
        }:
            raise ValueError(
                "self loops are limited to equivalence/version relations"
            )
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class IRHyperedge:
    hyperedge_id: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    kind: EdgeKind
    attributes: Mapping[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()
    confidence: float = 0.5

    def __post_init__(self) -> None:
        if not self.hyperedge_id.strip() or not self.sources or not self.targets:
            raise ValueError(
                "hyperedge_id, sources and targets are required"
            )
        if (
            len(set(self.sources)) != len(self.sources)
            or len(set(self.targets)) != len(self.targets)
        ):
            raise ValueError("hyperedge endpoints must be unique")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    object_id: str
    severity: str = "error"


class REIRGraph:
    def __init__(self, graph_id: str, *, schema_version: str = "0.2.0"):
        if not graph_id.strip():
            raise ValueError("graph_id is required")
        self.graph_id = graph_id
        self.schema_version = schema_version
        self.nodes: dict[str, IRNode] = {}
        self.edges: dict[str, IREdge] = {}
        self.hyperedges: dict[str, IRHyperedge] = {}

    def add_node(self, node: IRNode, *, replace: bool = False) -> None:
        if node.node_id in self.nodes and not replace:
            raise KeyError(f"duplicate node {node.node_id}")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: IREdge, *, replace: bool = False) -> None:
        if edge.edge_id in self.edges and not replace:
            raise KeyError(f"duplicate edge {edge.edge_id}")
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise KeyError("edge endpoints must exist")
        self.edges[edge.edge_id] = edge

    def add_hyperedge(
        self,
        edge: IRHyperedge,
        *,
        replace: bool = False,
    ) -> None:
        if edge.hyperedge_id in self.hyperedges and not replace:
            raise KeyError(f"duplicate hyperedge {edge.hyperedge_id}")
        missing = (set(edge.sources) | set(edge.targets)) - self.nodes.keys()
        if missing:
            raise KeyError(
                f"hyperedge endpoints missing: {sorted(missing)}"
            )
        self.hyperedges[edge.hyperedge_id] = edge

    def remove_node(self, node_id: str, *, cascade: bool = False) -> None:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        incident_edges = [
            key
            for key, edge in self.edges.items()
            if node_id in {edge.source, edge.target}
        ]
        incident_hyperedges = [
            key
            for key, edge in self.hyperedges.items()
            if node_id in edge.sources or node_id in edge.targets
        ]
        if (incident_edges or incident_hyperedges) and not cascade:
            raise ValueError("node has incident relations")
        for key in incident_edges:
            del self.edges[key]
        for key in incident_hyperedges:
            del self.hyperedges[key]
        del self.nodes[node_id]

    def neighbors(
        self,
        node_id: str,
        *,
        kinds: set[EdgeKind] | None = None,
        direction: str = "both",
    ) -> tuple[str, ...]:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        if direction not in {"in", "out", "both"}:
            raise ValueError("direction must be in, out or both")
        found: set[str] = set()
        for edge in self.edges.values():
            if kinds and edge.kind not in kinds:
                continue
            if direction in {"out", "both"} and edge.source == node_id:
                found.add(edge.target)
            if direction in {"in", "both"} and edge.target == node_id:
                found.add(edge.source)
        for edge in self.hyperedges.values():
            if kinds and edge.kind not in kinds:
                continue
            if direction in {"out", "both"} and node_id in edge.sources:
                found.update(edge.targets)
            if direction in {"in", "both"} and node_id in edge.targets:
                found.update(edge.sources)
        found.discard(node_id)
        return tuple(sorted(found))

    def query_nodes(
        self,
        *,
        kind: NodeKind | None = None,
        level: EpistemicLevel | None = None,
        predicate: Callable[[IRNode], bool] | None = None,
    ) -> tuple[IRNode, ...]:
        values: Iterable[IRNode] = self.nodes.values()
        if kind is not None:
            values = (node for node in values if node.kind is kind)
        if level is not None:
            values = (node for node in values if node.level is level)
        if predicate is not None:
            values = (node for node in values if predicate(node))
        return tuple(sorted(values, key=lambda node: node.node_id))

    def shortest_path(
        self,
        source: str,
        target: str,
    ) -> tuple[str, ...] | None:
        if source not in self.nodes or target not in self.nodes:
            raise KeyError("source and target must exist")
        queue = deque([(source, (source,))])
        visited = {source}
        while queue:
            current, path = queue.popleft()
            if current == target:
                return path
            for neighbor in self.neighbors(current, direction="out"):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + (neighbor,)))
        return None

    def strongly_connected_components(
        self,
    ) -> tuple[tuple[str, ...], ...]:
        index = 0
        stack: list[str] = []
        on_stack: set[str] = set()
        indices: dict[str, int] = {}
        lowlink: dict[str, int] = {}
        components: list[tuple[str, ...]] = []
        adjacency = {
            node: self.neighbors(node, direction="out")
            for node in self.nodes
        }

        def visit(node: str) -> None:
            nonlocal index
            indices[node] = lowlink[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)
            for neighbor in adjacency[node]:
                if neighbor not in indices:
                    visit(neighbor)
                    lowlink[node] = min(
                        lowlink[node],
                        lowlink[neighbor],
                    )
                elif neighbor in on_stack:
                    lowlink[node] = min(
                        lowlink[node],
                        indices[neighbor],
                    )
            if lowlink[node] == indices[node]:
                component: list[str] = []
                while True:
                    value = stack.pop()
                    on_stack.remove(value)
                    component.append(value)
                    if value == node:
                        break
                components.append(tuple(sorted(component)))

        for node in sorted(self.nodes):
            if node not in indices:
                visit(node)
        return tuple(sorted(components))

    def validate(self) -> tuple[ValidationIssue, ...]:
        issues: list[ValidationIssue] = []
        for edge in self.edges.values():
            if edge.source not in self.nodes or edge.target not in self.nodes:
                issues.append(
                    ValidationIssue(
                        "dangling_edge",
                        "edge references a missing node",
                        edge.edge_id,
                    )
                )
            if (
                edge.kind
                in {
                    EdgeKind.SUPPORTS,
                    EdgeKind.CAUSES,
                    EdgeKind.DERIVED_FROM,
                }
                and not edge.provenance
            ):
                issues.append(
                    ValidationIssue(
                        "missing_relation_provenance",
                        "high-impact relation lacks provenance",
                        edge.edge_id,
                        "warning",
                    )
                )
        for edge in self.hyperedges.values():
            missing = (
                set(edge.sources) | set(edge.targets)
            ) - self.nodes.keys()
            if missing:
                issues.append(
                    ValidationIssue(
                        "dangling_hyperedge",
                        f"missing nodes: {sorted(missing)}",
                        edge.hyperedge_id,
                    )
                )
        for node in self.nodes.values():
            if (
                node.level is EpistemicLevel.VERIFIED_WITHIN_DOMAIN
                and "valid_domain" not in node.attributes
            ):
                issues.append(
                    ValidationIssue(
                        "missing_valid_domain",
                        "verified node lacks valid_domain",
                        node.node_id,
                    )
                )
            if (
                node.kind is NodeKind.CLAIM
                and not self.neighbors(
                    node.node_id,
                    kinds={EdgeKind.SUPPORTS},
                    direction="in",
                )
            ):
                issues.append(
                    ValidationIssue(
                        "unsupported_claim",
                        "claim has no supporting evidence",
                        node.node_id,
                        "warning",
                    )
                )
        return tuple(issues)

    @property
    def provenance_coverage(self) -> float:
        objects: list[Any] = (
            list(self.nodes.values())
            + list(self.edges.values())
            + list(self.hyperedges.values())
        )
        if not objects:
            return 1.0
        return sum(bool(obj.provenance) for obj in objects) / len(objects)

    def canonical_dict(self) -> dict[str, Any]:
        def node_dict(node: IRNode) -> dict[str, Any]:
            data = asdict(node)
            data["kind"] = node.kind.value
            data["level"] = node.level.value
            data["provenance"] = list(node.provenance)
            return data

        def edge_dict(edge: IREdge | IRHyperedge) -> dict[str, Any]:
            data = asdict(edge)
            data["kind"] = edge.kind.value
            data["provenance"] = list(edge.provenance)
            return data

        return {
            "graph_id": self.graph_id,
            "schema_version": self.schema_version,
            "nodes": [
                node_dict(self.nodes[key])
                for key in sorted(self.nodes)
            ],
            "edges": [
                edge_dict(self.edges[key])
                for key in sorted(self.edges)
            ],
            "hyperedges": [
                edge_dict(self.hyperedges[key])
                for key in sorted(self.hyperedges)
            ],
        }

    @property
    def digest(self) -> str:
        payload = dumps(
            self.canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return sha256(payload.encode("utf-8")).hexdigest()

    def to_json(self, *, indent: int | None = 2) -> str:
        return dumps(
            self.canonical_dict(),
            sort_keys=True,
            indent=indent,
            ensure_ascii=False,
        )

    @classmethod
    def from_json(cls, text: str) -> "REIRGraph":
        data = loads(text)
        graph = cls(
            data["graph_id"],
            schema_version=data.get("schema_version", "0.2.0"),
        )
        for raw in data.get("nodes", []):
            raw = dict(raw)
            raw["kind"] = NodeKind(raw["kind"])
            raw["level"] = EpistemicLevel(raw["level"])
            raw["provenance"] = tuple(raw.get("provenance", []))
            graph.add_node(IRNode(**raw))
        for raw in data.get("edges", []):
            raw = dict(raw)
            raw["kind"] = EdgeKind(raw["kind"])
            raw["provenance"] = tuple(raw.get("provenance", []))
            graph.add_edge(IREdge(**raw))
        for raw in data.get("hyperedges", []):
            raw = dict(raw)
            raw["kind"] = EdgeKind(raw["kind"])
            raw["sources"] = tuple(raw["sources"])
            raw["targets"] = tuple(raw["targets"])
            raw["provenance"] = tuple(raw.get("provenance", []))
            graph.add_hyperedge(IRHyperedge(**raw))
        return graph

    def induced_subgraph(
        self,
        node_ids: Iterable[str],
        *,
        graph_id: str | None = None,
    ) -> "REIRGraph":
        selected = set(node_ids)
        missing = selected - self.nodes.keys()
        if missing:
            raise KeyError(f"unknown nodes: {sorted(missing)}")
        result = REIRGraph(
            graph_id or f"{self.graph_id}-subgraph",
            schema_version=self.schema_version,
        )
        for node_id in sorted(selected):
            result.add_node(self.nodes[node_id])
        for edge in self.edges.values():
            if edge.source in selected and edge.target in selected:
                result.add_edge(edge)
        for edge in self.hyperedges.values():
            if set(edge.sources) | set(edge.targets) <= selected:
                result.add_hyperedge(edge)
        return result

    def merge(
        self,
        other: "REIRGraph",
        *,
        conflict: str = "error",
    ) -> "REIRGraph":
        if conflict not in {"error", "left", "right"}:
            raise ValueError("conflict must be error, left or right")
        result = REIRGraph(
            f"{self.graph_id}+{other.graph_id}",
            schema_version=max(self.schema_version, other.schema_version),
        )
        for source in (self, other):
            for node in source.nodes.values():
                if (
                    node.node_id in result.nodes
                    and result.nodes[node.node_id] != node
                ):
                    if conflict == "error":
                        raise ValueError(
                            f"node conflict: {node.node_id}"
                        )
                    if conflict == "left" and source is other:
                        continue
                result.add_node(node, replace=True)
            for edge in source.edges.values():
                if (
                    edge.edge_id in result.edges
                    and result.edges[edge.edge_id] != edge
                ):
                    if conflict == "error":
                        raise ValueError(
                            f"edge conflict: {edge.edge_id}"
                        )
                    if conflict == "left" and source is other:
                        continue
                result.add_edge(edge, replace=True)
            for edge in source.hyperedges.values():
                if (
                    edge.hyperedge_id in result.hyperedges
                    and result.hyperedges[edge.hyperedge_id] != edge
                ):
                    if conflict == "error":
                        raise ValueError(
                            f"hyperedge conflict: {edge.hyperedge_id}"
                        )
                    if conflict == "left" and source is other:
                        continue
                result.add_hyperedge(edge, replace=True)
        return result


def make_claim_bundle(
    graph_id: str,
    claim_id: str,
    statement: str,
    evidence: Iterable[tuple[str, str]],
) -> REIRGraph:
    evidence = tuple(evidence)
    graph = REIRGraph(graph_id)
    graph.add_node(
        IRNode(
            claim_id,
            NodeKind.CLAIM,
            statement,
            EpistemicLevel.INFERRED,
            provenance=tuple(item[0] for item in evidence),
            uncertainty=0.5,
        )
    )
    for index, (source, description) in enumerate(evidence):
        evidence_id = f"{claim_id}-evidence-{index}"
        graph.add_node(
            IRNode(
                evidence_id,
                NodeKind.EVIDENCE,
                description,
                EpistemicLevel.OBSERVED,
                provenance=(source,),
                uncertainty=0.0,
            )
        )
        graph.add_edge(
            IREdge(
                f"support-{index}",
                evidence_id,
                claim_id,
                EdgeKind.SUPPORTS,
                provenance=(source,),
                confidence=1.0,
            )
        )
    return graph
