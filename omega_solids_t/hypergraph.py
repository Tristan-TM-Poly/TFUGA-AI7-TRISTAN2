from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .genome import SolidGenome


@dataclass(frozen=True, slots=True)
class SolidNode:
    identifier: str
    kind: str
    label: str
    scale: str
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.identifier or not self.kind or not self.label:
            raise ValueError("Node identifier, kind, and label are required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.identifier,
            "kind": self.kind,
            "label": self.label,
            "scale": self.scale,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class SolidHyperEdge:
    identifier: str
    kind: str
    members: tuple[str, ...]
    directed: bool = False
    weight: float = 1.0
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.identifier or not self.kind:
            raise ValueError("Hyperedge identifier and kind are required")
        if len(set(self.members)) < 2:
            raise ValueError("A hyperedge must connect at least two distinct members")
        if self.weight < 0:
            raise ValueError("Hyperedge weight cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.identifier,
            "kind": self.kind,
            "members": list(self.members),
            "directed": self.directed,
            "weight": self.weight,
            "attributes": dict(self.attributes),
        }


class SolidHyperGraph:
    """Dependency-free material hypergraph with deterministic serialization."""

    def __init__(self) -> None:
        self._nodes: dict[str, SolidNode] = {}
        self._edges: dict[str, SolidHyperEdge] = {}
        self._incidence: dict[str, set[str]] = {}

    @property
    def nodes(self) -> tuple[SolidNode, ...]:
        return tuple(self._nodes[key] for key in sorted(self._nodes))

    @property
    def edges(self) -> tuple[SolidHyperEdge, ...]:
        return tuple(self._edges[key] for key in sorted(self._edges))

    def add_node(self, node: SolidNode, *, replace: bool = False) -> None:
        if node.identifier in self._nodes and not replace:
            raise ValueError(f"Duplicate node: {node.identifier}")
        self._nodes[node.identifier] = node
        self._incidence.setdefault(node.identifier, set())

    def add_edge(self, edge: SolidHyperEdge, *, replace: bool = False) -> None:
        if edge.identifier in self._edges and not replace:
            raise ValueError(f"Duplicate edge: {edge.identifier}")
        missing = [member for member in edge.members if member not in self._nodes]
        if missing:
            raise KeyError(f"Hyperedge references missing nodes: {missing}")
        previous = self._edges.get(edge.identifier)
        if previous is not None:
            for member in previous.members:
                self._incidence[member].discard(edge.identifier)
        self._edges[edge.identifier] = edge
        for member in edge.members:
            self._incidence[member].add(edge.identifier)

    def remove_edge(self, identifier: str) -> None:
        edge = self._edges.pop(identifier)
        for member in edge.members:
            self._incidence[member].discard(identifier)

    def incident_edges(self, node_identifier: str) -> tuple[SolidHyperEdge, ...]:
        if node_identifier not in self._nodes:
            raise KeyError(node_identifier)
        return tuple(
            self._edges[identifier]
            for identifier in sorted(self._incidence[node_identifier])
        )

    def neighbors(self, node_identifier: str, *, edge_kind: str | None = None) -> tuple[str, ...]:
        result: set[str] = set()
        for edge in self.incident_edges(node_identifier):
            if edge_kind is not None and edge.kind != edge_kind:
                continue
            result.update(edge.members)
        result.discard(node_identifier)
        return tuple(sorted(result))

    def shortest_hyperpath(self, source: str, target: str) -> tuple[str, ...] | None:
        if source not in self._nodes or target not in self._nodes:
            raise KeyError("Both source and target must be graph nodes")
        queue: deque[str] = deque([source])
        parent: dict[str, str | None] = {source: None}
        while queue:
            current = queue.popleft()
            if current == target:
                break
            for neighbor in self.neighbors(current):
                if neighbor not in parent:
                    parent[neighbor] = current
                    queue.append(neighbor)
        if target not in parent:
            return None
        path: list[str] = []
        cursor: str | None = target
        while cursor is not None:
            path.append(cursor)
            cursor = parent[cursor]
        return tuple(reversed(path))

    def connected_components(self) -> tuple[tuple[str, ...], ...]:
        unseen = set(self._nodes)
        components: list[tuple[str, ...]] = []
        while unseen:
            start = min(unseen)
            queue = deque([start])
            component: set[str] = {start}
            unseen.remove(start)
            while queue:
                current = queue.popleft()
                for neighbor in self.neighbors(current):
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)
            components.append(tuple(sorted(component)))
        return tuple(components)

    def validate(self) -> tuple[str, ...]:
        issues: list[str] = []
        for edge in self.edges:
            for member in edge.members:
                if member not in self._nodes:
                    issues.append(f"edge:{edge.identifier}:missing:{member}")
        for node_id, edge_ids in self._incidence.items():
            if node_id not in self._nodes:
                issues.append(f"incidence:orphan-node:{node_id}")
            for edge_id in edge_ids:
                if edge_id not in self._edges:
                    issues.append(f"incidence:orphan-edge:{edge_id}")
                elif node_id not in self._edges[edge_id].members:
                    issues.append(f"incidence:mismatch:{node_id}:{edge_id}")
        return tuple(sorted(issues))

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "hyperedges": [edge.to_dict() for edge in self.edges],
            "summary": {
                "node_count": len(self._nodes),
                "hyperedge_count": len(self._edges),
                "component_count": len(self.connected_components()),
            },
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SolidHyperGraph":
        graph = cls()
        for item in payload.get("nodes", []):
            graph.add_node(
                SolidNode(
                    identifier=str(item["id"]),
                    kind=str(item["kind"]),
                    label=str(item["label"]),
                    scale=str(item.get("scale", "unknown")),
                    attributes=dict(item.get("attributes", {})),
                )
            )
        for item in payload.get("hyperedges", []):
            graph.add_edge(
                SolidHyperEdge(
                    identifier=str(item["id"]),
                    kind=str(item["kind"]),
                    members=tuple(str(value) for value in item["members"]),
                    directed=bool(item.get("directed", False)),
                    weight=float(item.get("weight", 1.0)),
                    attributes=dict(item.get("attributes", {})),
                )
            )
        return graph

    def write_json(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return target

    def to_graphml(self) -> str:
        """Project hyperedges to explicit edge-nodes in GraphML.

        GraphML is graph-based; representing hyperedges as nodes preserves
        memberships without pretending they are pairwise physical bonds.
        """

        def escape(value: Any) -> str:
            return (
                str(value)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
            )

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '  <key id="kind" for="all" attr.name="kind" attr.type="string"/>',
            '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
            '  <graph id="solid-hypergraph" edgedefault="undirected">',
        ]
        for node in self.nodes:
            lines.extend(
                [
                    f'    <node id="{escape(node.identifier)}">',
                    f'      <data key="kind">{escape(node.kind)}</data>',
                    f'      <data key="label">{escape(node.label)}</data>',
                    "    </node>",
                ]
            )
        for edge in self.edges:
            edge_node = f"hyperedge::{edge.identifier}"
            lines.extend(
                [
                    f'    <node id="{escape(edge_node)}">',
                    f'      <data key="kind">hyperedge:{escape(edge.kind)}</data>',
                    f'      <data key="label">{escape(edge.identifier)}</data>',
                    "    </node>",
                ]
            )
            for index, member in enumerate(edge.members):
                lines.append(
                    f'    <edge id="inc::{escape(edge.identifier)}::{index}" '
                    f'source="{escape(edge_node)}" target="{escape(member)}"/>'
                )
        lines.extend(["  </graph>", "</graphml>"])
        return "\n".join(lines) + "\n"

    @classmethod
    def from_genome(cls, genome: SolidGenome) -> "SolidHyperGraph":
        graph = cls()
        root_id = f"solid::{genome.identifier}"
        graph.add_node(
            SolidNode(
                root_id,
                "solid",
                genome.name,
                "system",
                {
                    "family": genome.family,
                    "order": genome.order.value,
                    "dimensionality": genome.dimensionality.value,
                    "status": genome.status.value,
                },
            )
        )

        composition_nodes: list[str] = []
        for index, component in enumerate(genome.composition):
            node_id = f"component::{index}::{component.species}"
            composition_nodes.append(node_id)
            graph.add_node(
                SolidNode(
                    node_id,
                    "composition_component",
                    component.species,
                    "atomic_or_molecular",
                    component.to_dict(),
                )
            )
        if composition_nodes:
            graph.add_edge(
                SolidHyperEdge(
                    "composition",
                    "constitutes",
                    tuple([root_id, *composition_nodes]),
                    attributes={"formula": genome.formula},
                )
            )

        phase_nodes: list[str] = []
        for index, phase in enumerate(genome.phases):
            node_id = f"phase::{index}::{phase.name}"
            phase_nodes.append(node_id)
            graph.add_node(
                SolidNode(node_id, "phase", phase.name, "mesoscale", phase.to_dict())
            )
        if phase_nodes:
            graph.add_edge(
                SolidHyperEdge(
                    "phase-assembly",
                    "phase_coexistence",
                    tuple([root_id, *phase_nodes]),
                )
            )

        defect_nodes: list[str] = []
        for index, defect in enumerate(genome.defects):
            node_id = f"defect::{index}::{defect.kind.value}"
            defect_nodes.append(node_id)
            graph.add_node(
                SolidNode(
                    node_id,
                    "defect",
                    defect.kind.value,
                    "multiscale",
                    defect.to_dict(),
                )
            )
        for index, node_id in enumerate(defect_nodes):
            members = [root_id, node_id]
            if phase_nodes:
                members.append(phase_nodes[index % len(phase_nodes)])
            graph.add_edge(
                SolidHyperEdge(
                    f"defect-context::{index}",
                    "defect_context",
                    tuple(members),
                    weight=max(0.01, genome.defects[index].criticality),
                )
            )

        for index, interface in enumerate(genome.interfaces):
            node_id = f"interface::{index}::{interface.name}"
            graph.add_node(
                SolidNode(
                    node_id,
                    "interface",
                    interface.name,
                    "interfacial",
                    interface.to_dict(),
                )
            )
            members = [root_id, node_id]
            matched = [
                phase_id
                for phase_id, phase in zip(phase_nodes, genome.phases)
                if phase.name in interface.between
            ]
            members.extend(matched)
            if len(set(members)) < 2:
                continue
            graph.add_edge(
                SolidHyperEdge(
                    f"interface-context::{index}",
                    "interface_coupling",
                    tuple(dict.fromkeys(members)),
                )
            )

        for index, record in enumerate(genome.properties):
            node_id = f"property::{index}::{record.name}"
            graph.add_node(
                SolidNode(
                    node_id,
                    "observable",
                    record.name,
                    "measurement",
                    record.to_dict(),
                )
            )
            context_members = [root_id, node_id]
            if defect_nodes and record.domain.value in {"mechanical", "durability"}:
                context_members.extend(defect_nodes[: min(3, len(defect_nodes))])
            if phase_nodes:
                context_members.extend(phase_nodes[: min(3, len(phase_nodes))])
            graph.add_edge(
                SolidHyperEdge(
                    f"property-emergence::{index}",
                    "emergent_property",
                    tuple(dict.fromkeys(context_members)),
                    attributes={"domain": record.domain.value},
                )
            )

        process_nodes: list[str] = []
        for index, step in enumerate(genome.process):
            label = str(step.get("name", step.get("operation", f"step-{index}")))
            node_id = f"process::{index}::{label}"
            process_nodes.append(node_id)
            graph.add_node(SolidNode(node_id, "process", label, "manufacturing", dict(step)))
        for index in range(len(process_nodes) - 1):
            graph.add_edge(
                SolidHyperEdge(
                    f"process-sequence::{index}",
                    "process_transition",
                    (process_nodes[index], process_nodes[index + 1]),
                    directed=True,
                )
            )
        if process_nodes:
            graph.add_edge(
                SolidHyperEdge(
                    "process-to-solid",
                    "produces",
                    (process_nodes[-1], root_id),
                    directed=True,
                )
            )
        return graph
