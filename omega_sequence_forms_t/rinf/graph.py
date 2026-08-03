"""Versioned representation hypergraph for analytic sequence forms."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping, Sequence


class NodeKind(str, Enum):
    SEQUENCE = "sequence"
    FORM = "form"
    OPERATOR = "operator"
    GENERATING_FUNCTION = "generating_function"
    ASYMPTOTIC = "asymptotic"
    INTEGRAL = "integral"
    ALGORITHM = "algorithm"
    EVIDENCE = "evidence"
    RESIDUAL = "residual"
    COUNTEREXAMPLE = "counterexample"
    PROOF_OBLIGATION = "proof_obligation"


class EdgeKind(str, Enum):
    REPRESENTS = "represents"
    TRANSFORMS_TO = "transforms_to"
    COMPILES_TO = "compiles_to"
    EQUIVALENT_IF = "equivalent_if"
    VALIDATED_BY = "validated_by"
    FALSIFIED_BY = "falsified_by"
    DEPENDS_ON = "depends_on"
    RESIDUAL_OF = "residual_of"
    PROVES = "proves"
    APPROXIMATES = "approximates"


@dataclass(frozen=True)
class RepresentationNode:
    node_id: str
    kind: NodeKind
    label: str
    payload: Mapping[str, Any]
    assumptions: tuple[str, ...] = ()
    risk_tags: tuple[str, ...] = ()
    provenance: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "kind": self.kind.value,
            "label": self.label,
            "payload": dict(self.payload),
            "assumptions": list(self.assumptions),
            "risk_tags": list(self.risk_tags),
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class RepresentationEdge:
    edge_id: str
    kind: EdgeKind
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    transformation_id: str
    exact: bool
    invertible: bool
    assumptions: tuple[str, ...]
    proof_obligations: tuple[str, ...]
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.sources or not self.targets:
            raise ValueError("hyperedge requires at least one source and target")
        if self.invertible and not self.exact:
            raise ValueError("an invertible edge must be exact")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        return payload


@dataclass
class RepresentationHypergraph:
    graph_id: str
    nodes: dict[str, RepresentationNode] = field(default_factory=dict)
    edges: dict[str, RepresentationEdge] = field(default_factory=dict)
    version: int = 1

    def add_node(self, node: RepresentationNode) -> None:
        existing = self.nodes.get(node.node_id)
        if existing is not None and existing != node:
            raise ValueError(f"node ID collision: {node.node_id}")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: RepresentationEdge) -> None:
        existing = self.edges.get(edge.edge_id)
        if existing is not None and existing != edge:
            raise ValueError(f"edge ID collision: {edge.edge_id}")
        unknown = [node for node in edge.sources + edge.targets if node not in self.nodes]
        if unknown:
            raise KeyError(f"edge references unknown nodes: {unknown}")
        self.edges[edge.edge_id] = edge

    def incident_edges(self, node_id: str) -> tuple[RepresentationEdge, ...]:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        return tuple(
            edge
            for edge in self.edges.values()
            if node_id in edge.sources or node_id in edge.targets
        )

    def reachable(
        self,
        seeds: Iterable[str],
        *,
        edge_kinds: Iterable[EdgeKind] | None = None,
        exact_only: bool = False,
    ) -> set[str]:
        allowed = None if edge_kinds is None else set(edge_kinds)
        reached = set(seeds)
        unknown = reached - self.nodes.keys()
        if unknown:
            raise KeyError(f"unknown seed nodes: {sorted(unknown)}")
        changed = True
        while changed:
            changed = False
            for edge in self.edges.values():
                if allowed is not None and edge.kind not in allowed:
                    continue
                if exact_only and not edge.exact:
                    continue
                if set(edge.sources) <= reached:
                    for target in edge.targets:
                        if target not in reached:
                            reached.add(target)
                            changed = True
        return reached

    def validate(self) -> list[str]:
        errors: list[str] = []
        for edge in self.edges.values():
            for node in edge.sources + edge.targets:
                if node not in self.nodes:
                    errors.append(f"{edge.edge_id}: unknown node {node}")
            if edge.kind == EdgeKind.PROVES and not edge.exact:
                errors.append(f"{edge.edge_id}: proof edge cannot be approximate")
            if edge.kind == EdgeKind.APPROXIMATES and edge.exact:
                errors.append(f"{edge.edge_id}: approximation edge marked exact")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "omega-sequence-forms-representation-hypergraph/1",
            "graph_id": self.graph_id,
            "version": self.version,
            "nodes": [self.nodes[key].to_dict() for key in sorted(self.nodes)],
            "edges": [self.edges[key].to_dict() for key in sorted(self.edges)],
            "validation_errors": self.validate(),
            "global_identity_proved": False,
        }

    def digest(self) -> str:
        canonical = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()

    def graphml(self) -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            f'  <graph id="{_xml(self.graph_id)}" edgedefault="directed">',
        ]
        for node_id in sorted(self.nodes):
            node = self.nodes[node_id]
            lines.append(f'    <node id="{_xml(node.node_id)}">')
            lines.append(f'      <data key="kind">{_xml(node.kind.value)}</data>')
            lines.append(f'      <data key="label">{_xml(node.label)}</data>')
            lines.append('    </node>')
        for edge_id in sorted(self.edges):
            edge = self.edges[edge_id]
            for source in edge.sources:
                for target in edge.targets:
                    projected_id = f"{edge.edge_id}:{source}:{target}"
                    lines.append(
                        f'    <edge id="{_xml(projected_id)}" source="{_xml(source)}" target="{_xml(target)}">'
                    )
                    lines.append(f'      <data key="kind">{_xml(edge.kind.value)}</data>')
                    lines.append(f'      <data key="hyperedge">{_xml(edge.edge_id)}</data>')
                    lines.append('    </edge>')
        lines.extend(['  </graph>', '</graphml>', ''])
        return "\n".join(lines)


def _xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def sequence_graph_fixture() -> RepresentationHypergraph:
    graph = RepresentationHypergraph("fixture.fibonacci")
    graph.add_node(RepresentationNode("seq", NodeKind.SEQUENCE, "finite prefix", {"terms": [0, 1, 1, 2, 3, 5]}))
    graph.add_node(RepresentationNode("rec", NodeKind.OPERATOR, "linear recurrence", {"expression": "a[n+2]=a[n+1]+a[n]"}))
    graph.add_node(RepresentationNode("gf", NodeKind.GENERATING_FUNCTION, "rational OGF", {"expression": "z/(1-z-z^2)"}))
    graph.add_node(RepresentationNode("proof", NodeKind.PROOF_OBLIGATION, "global induction", {"completed": False}))
    graph.add_edge(RepresentationEdge("fit", EdgeKind.REPRESENTS, ("seq",), ("rec",), "infer.recurrence", False, False, ("finite_prefix",), ("prove_all_n",)))
    graph.add_edge(RepresentationEdge("compile", EdgeKind.COMPILES_TO, ("rec",), ("gf",), "recurrence_to_ogf", True, False, ("initial_conditions",), ("verify_numerator",)))
    graph.add_edge(RepresentationEdge("obligation", EdgeKind.DEPENDS_ON, ("rec",), ("proof",), "oak_proof_gate", True, False, (), ("complete_induction",)))
    return graph
