from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field, replace
from enum import Enum
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .canonical import (
    CanonicalizationError,
    assert_no_secret_keys,
    canonical_hash,
    normalize_text,
    stable_unique,
)


class NodeType(str, Enum):
    COMPANY = "company"
    ORGANIZATION = "organization"
    DIVISION = "division"
    CONTACT = "contact"
    CONSENT = "consent"
    OPPORTUNITY = "opportunity"
    ASSET = "asset"
    CLAIM = "claim"
    EVIDENCE = "evidence"
    OUTREACH_CASE = "outreach_case"
    MESSAGE = "message"
    REPLY = "reply"
    MEETING = "meeting"
    PROPOSAL = "proposal"
    PILOT = "pilot"
    CONTRACT = "contract"
    PAYMENT = "payment"
    INCIDENT = "incident"


class EdgeType(str, Enum):
    OWNS = "owns"
    BELONGS_TO = "belongs_to"
    RESPONSIBLE_FOR = "responsible_for"
    CONTRIBUTES_TO = "contributes_to"
    TARGETS = "targets"
    HAS_CONTACT = "has_contact"
    HAS_CONSENT = "has_consent"
    PROPOSES = "proposes"
    SUPPORTED_BY = "supported_by"
    ASSERTS = "asserts"
    ADDRESSES = "addresses"
    SENT_TO = "sent_to"
    REPLIES_TO = "replies_to"
    SCHEDULES = "schedules"
    PRODUCES = "produces"
    SUPERSEDES = "supersedes"
    DUPLICATE_OF = "duplicate_of"
    BLOCKED_BY = "blocked_by"
    CAUSED = "caused"
    RECONCILES = "reconciles"


@dataclass(frozen=True, slots=True)
class GraphNode:
    node_id: str
    node_type: NodeType
    label: str
    public_attributes: Mapping[str, Any] = field(default_factory=dict)
    private_reference_hashes: tuple[str, ...] = ()
    evidence_hashes: tuple[str, ...] = ()
    version: int = 1

    def __post_init__(self) -> None:
        node_id = normalize_text(self.node_id)
        label = normalize_text(self.label)
        if not node_id or not label:
            raise CanonicalizationError("graph node_id and label are required")
        if self.version < 1:
            raise CanonicalizationError("graph node version must be positive")
        assert_no_secret_keys(self.public_attributes)
        object.__setattr__(self, "node_id", node_id)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "public_attributes", dict(self.public_attributes))
        object.__setattr__(
            self, "private_reference_hashes", tuple(sorted(set(self.private_reference_hashes)))
        )
        object.__setattr__(self, "evidence_hashes", tuple(sorted(set(self.evidence_hashes))))

    @property
    def node_hash(self) -> str:
        return canonical_hash(self)

    def update(self, *, public_attributes: Mapping[str, Any]) -> "GraphNode":
        merged = dict(self.public_attributes)
        merged.update(public_attributes)
        return replace(self, public_attributes=merged, version=self.version + 1)


@dataclass(frozen=True, slots=True)
class GraphEdge:
    edge_id: str
    edge_type: EdgeType
    source_id: str
    target_id: str
    weight: float = 1.0
    confidence: float = 1.0
    evidence_hashes: tuple[str, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        edge_id = normalize_text(self.edge_id)
        source_id = normalize_text(self.source_id)
        target_id = normalize_text(self.target_id)
        if not edge_id or not source_id or not target_id:
            raise CanonicalizationError("graph edge identifiers are required")
        if source_id == target_id and self.edge_type is not EdgeType.DUPLICATE_OF:
            raise CanonicalizationError("self edges are allowed only for explicit duplicate markers")
        if not 0.0 <= self.weight <= 1.0:
            raise CanonicalizationError("graph edge weight must be between 0 and 1")
        if not 0.0 <= self.confidence <= 1.0:
            raise CanonicalizationError("graph edge confidence must be between 0 and 1")
        assert_no_secret_keys(self.attributes)
        object.__setattr__(self, "edge_id", edge_id)
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "target_id", target_id)
        object.__setattr__(self, "evidence_hashes", tuple(sorted(set(self.evidence_hashes))))
        object.__setattr__(self, "attributes", dict(self.attributes))

    @property
    def edge_hash(self) -> str:
        return canonical_hash(self)


@dataclass(frozen=True, slots=True)
class Hyperedge:
    hyperedge_id: str
    relation: str
    participant_ids: tuple[str, ...]
    roles: Mapping[str, str]
    confidence: float
    evidence_hashes: tuple[str, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        hyperedge_id = normalize_text(self.hyperedge_id)
        relation = normalize_text(self.relation).casefold().replace(" ", "_")
        participants = stable_unique(self.participant_ids)
        if not hyperedge_id or not relation:
            raise CanonicalizationError("hyperedge identifier and relation are required")
        if len(participants) < 2:
            raise CanonicalizationError("hyperedge requires at least two participants")
        if set(self.roles) - set(participants):
            raise CanonicalizationError("hyperedge roles reference unknown participants")
        if not 0.0 <= self.confidence <= 1.0:
            raise CanonicalizationError("hyperedge confidence must be between 0 and 1")
        assert_no_secret_keys(self.attributes)
        object.__setattr__(self, "hyperedge_id", hyperedge_id)
        object.__setattr__(self, "relation", relation)
        object.__setattr__(self, "participant_ids", participants)
        object.__setattr__(self, "roles", dict(sorted(self.roles.items())))
        object.__setattr__(self, "evidence_hashes", tuple(sorted(set(self.evidence_hashes))))
        object.__setattr__(self, "attributes", dict(self.attributes))

    @property
    def hyperedge_hash(self) -> str:
        return canonical_hash(self)


@dataclass(frozen=True, slots=True)
class GraphAudit:
    valid: bool
    node_count: int
    edge_count: int
    hyperedge_count: int
    connected_components: int
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def audit_hash(self) -> str:
        return canonical_hash(self)


class RelationshipGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._hyperedges: dict[str, Hyperedge] = {}

    @property
    def nodes(self) -> tuple[GraphNode, ...]:
        return tuple(self._nodes[key] for key in sorted(self._nodes))

    @property
    def edges(self) -> tuple[GraphEdge, ...]:
        return tuple(self._edges[key] for key in sorted(self._edges))

    @property
    def hyperedges(self) -> tuple[Hyperedge, ...]:
        return tuple(self._hyperedges[key] for key in sorted(self._hyperedges))

    @property
    def graph_hash(self) -> str:
        return canonical_hash(self.to_mapping())

    def add_node(self, node: GraphNode) -> None:
        existing = self._nodes.get(node.node_id)
        if existing is not None and existing.node_hash != node.node_hash:
            raise CanonicalizationError(f"node_id already exists with different content: {node.node_id}")
        self._nodes[node.node_id] = node

    def update_node(self, node_id: str, attributes: Mapping[str, Any]) -> GraphNode:
        if node_id not in self._nodes:
            raise CanonicalizationError(f"unknown node_id: {node_id}")
        updated = self._nodes[node_id].update(public_attributes=attributes)
        self._nodes[node_id] = updated
        return updated

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
            raise CanonicalizationError("edge endpoints must exist before edge insertion")
        existing = self._edges.get(edge.edge_id)
        if existing is not None and existing.edge_hash != edge.edge_hash:
            raise CanonicalizationError(f"edge_id already exists with different content: {edge.edge_id}")
        self._edges[edge.edge_id] = edge

    def add_hyperedge(self, hyperedge: Hyperedge) -> None:
        missing = set(hyperedge.participant_ids) - set(self._nodes)
        if missing:
            raise CanonicalizationError(f"hyperedge references missing nodes: {sorted(missing)}")
        existing = self._hyperedges.get(hyperedge.hyperedge_id)
        if existing is not None and existing.hyperedge_hash != hyperedge.hyperedge_hash:
            raise CanonicalizationError(
                f"hyperedge_id already exists with different content: {hyperedge.hyperedge_id}"
            )
        self._hyperedges[hyperedge.hyperedge_id] = hyperedge

    def neighbors(
        self,
        node_id: str,
        *,
        edge_types: Iterable[EdgeType] | None = None,
        direction: str = "both",
    ) -> tuple[GraphNode, ...]:
        if node_id not in self._nodes:
            raise CanonicalizationError(f"unknown node_id: {node_id}")
        if direction not in {"in", "out", "both"}:
            raise CanonicalizationError("graph direction must be in, out or both")
        allowed = set(edge_types) if edge_types is not None else None
        identifiers: set[str] = set()
        for edge in self._edges.values():
            if allowed is not None and edge.edge_type not in allowed:
                continue
            if direction in {"out", "both"} and edge.source_id == node_id:
                identifiers.add(edge.target_id)
            if direction in {"in", "both"} and edge.target_id == node_id:
                identifiers.add(edge.source_id)
        return tuple(self._nodes[identifier] for identifier in sorted(identifiers))

    def shortest_path(
        self,
        source_id: str,
        target_id: str,
        *,
        allowed_edge_types: Iterable[EdgeType] | None = None,
        maximum_depth: int = 12,
    ) -> tuple[str, ...] | None:
        if source_id not in self._nodes or target_id not in self._nodes:
            raise CanonicalizationError("shortest path endpoints must exist")
        if maximum_depth < 1:
            raise CanonicalizationError("maximum_depth must be positive")
        if source_id == target_id:
            return (source_id,)
        allowed = set(allowed_edge_types) if allowed_edge_types is not None else None
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in self._edges.values():
            if allowed is not None and edge.edge_type not in allowed:
                continue
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)
        queue: deque[tuple[str, tuple[str, ...]]] = deque([(source_id, (source_id,))])
        visited = {source_id}
        while queue:
            current, path = queue.popleft()
            if len(path) > maximum_depth:
                continue
            for neighbor in sorted(adjacency[current]):
                if neighbor in visited:
                    continue
                next_path = (*path, neighbor)
                if neighbor == target_id:
                    return next_path
                visited.add(neighbor)
                queue.append((neighbor, next_path))
        return None

    def subgraph(self, node_ids: Iterable[str]) -> "RelationshipGraph":
        selected = set(node_ids)
        missing = selected - set(self._nodes)
        if missing:
            raise CanonicalizationError(f"subgraph references missing nodes: {sorted(missing)}")
        graph = RelationshipGraph()
        for identifier in sorted(selected):
            graph.add_node(self._nodes[identifier])
        for edge in self._edges.values():
            if edge.source_id in selected and edge.target_id in selected:
                graph.add_edge(edge)
        for hyperedge in self._hyperedges.values():
            if set(hyperedge.participant_ids).issubset(selected):
                graph.add_hyperedge(hyperedge)
        return graph

    def connected_components(self) -> tuple[tuple[str, ...], ...]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in self._edges.values():
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)
        for hyperedge in self._hyperedges.values():
            participants = hyperedge.participant_ids
            for index, source in enumerate(participants):
                for target in participants[index + 1 :]:
                    adjacency[source].add(target)
                    adjacency[target].add(source)
        remaining = set(self._nodes)
        components: list[tuple[str, ...]] = []
        while remaining:
            root = min(remaining)
            queue = deque([root])
            component: set[str] = set()
            while queue:
                current = queue.popleft()
                if current in component:
                    continue
                component.add(current)
                remaining.discard(current)
                queue.extend(sorted(adjacency[current] - component))
            components.append(tuple(sorted(component)))
        return tuple(sorted(components, key=lambda component: (len(component), component)))

    def audit(self) -> GraphAudit:
        errors: list[str] = []
        warnings: list[str] = []
        for edge in self._edges.values():
            if edge.source_id not in self._nodes:
                errors.append(f"edge {edge.edge_id} missing source node")
            if edge.target_id not in self._nodes:
                errors.append(f"edge {edge.edge_id} missing target node")
            if edge.confidence < 0.35:
                warnings.append(f"edge {edge.edge_id} has low confidence")
        for hyperedge in self._hyperedges.values():
            missing = set(hyperedge.participant_ids) - set(self._nodes)
            if missing:
                errors.append(f"hyperedge {hyperedge.hyperedge_id} missing nodes {sorted(missing)}")
            if hyperedge.confidence < 0.35:
                warnings.append(f"hyperedge {hyperedge.hyperedge_id} has low confidence")
        components = self.connected_components()
        if len(components) > 1:
            warnings.append(f"graph contains {len(components)} disconnected components")
        duplicate_edges: dict[tuple[EdgeType, str, str], str] = {}
        for edge in self._edges.values():
            key = (edge.edge_type, edge.source_id, edge.target_id)
            if key in duplicate_edges:
                errors.append(
                    f"duplicate semantic edge: {edge.edge_id} and {duplicate_edges[key]}"
                )
            duplicate_edges[key] = edge.edge_id
        return GraphAudit(
            valid=not errors,
            node_count=len(self._nodes),
            edge_count=len(self._edges),
            hyperedge_count=len(self._hyperedges),
            connected_components=len(components),
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "nodes": [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type.value,
                    "label": node.label,
                    "public_attributes": dict(node.public_attributes),
                    "private_reference_hashes": list(node.private_reference_hashes),
                    "evidence_hashes": list(node.evidence_hashes),
                    "version": node.version,
                    "node_hash": node.node_hash,
                }
                for node in self.nodes
            ],
            "edges": [
                {
                    "edge_id": edge.edge_id,
                    "edge_type": edge.edge_type.value,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "weight": edge.weight,
                    "confidence": edge.confidence,
                    "evidence_hashes": list(edge.evidence_hashes),
                    "attributes": dict(edge.attributes),
                    "edge_hash": edge.edge_hash,
                }
                for edge in self.edges
            ],
            "hyperedges": [
                {
                    "hyperedge_id": hyperedge.hyperedge_id,
                    "relation": hyperedge.relation,
                    "participant_ids": list(hyperedge.participant_ids),
                    "roles": dict(hyperedge.roles),
                    "confidence": hyperedge.confidence,
                    "evidence_hashes": list(hyperedge.evidence_hashes),
                    "attributes": dict(hyperedge.attributes),
                    "hyperedge_hash": hyperedge.hyperedge_hash,
                }
                for hyperedge in self.hyperedges
            ],
            "graph_hash": canonical_hash(
                {
                    "nodes": [node.node_hash for node in self.nodes],
                    "edges": [edge.edge_hash for edge in self.edges],
                    "hyperedges": [edge.hyperedge_hash for edge in self.hyperedges],
                }
            ),
        }

    def write_json(self, path: Path) -> None:
        audit = self.audit()
        if not audit.valid:
            raise CanonicalizationError("cannot serialize an invalid graph")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_mapping(), ensure_ascii=False, sort_keys=True, indent=2),
            encoding="utf-8",
        )


def responsibility_hyperedge(
    *,
    hyperedge_id: str,
    opportunity_id: str,
    owner_company_id: str,
    contributor_company_ids: Sequence[str],
    evidence_hashes: Sequence[str] = (),
) -> Hyperedge:
    participants = (opportunity_id, owner_company_id, *contributor_company_ids)
    roles = {opportunity_id: "subject", owner_company_id: "owner"}
    roles.update({company_id: "contributor" for company_id in contributor_company_ids})
    return Hyperedge(
        hyperedge_id=hyperedge_id,
        relation="company_responsibility",
        participant_ids=tuple(participants),
        roles=roles,
        confidence=1.0,
        evidence_hashes=tuple(evidence_hashes),
    )
