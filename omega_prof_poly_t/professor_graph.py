"""ProfessorGraph-Poly: lightweight interdisciplinary hypergraph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Node:
    node_id: str
    kind: str
    label: str
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class HyperEdge:
    edge_id: str
    relation: str
    node_ids: Tuple[str, ...]
    weight: float = 1.0


@dataclass
class ProfessorGraph:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: Dict[str, HyperEdge] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: HyperEdge) -> None:
        missing = [node_id for node_id in edge.node_ids if node_id not in self.nodes]
        if missing:
            raise ValueError(f"edge references missing nodes: {missing}")
        self.edges[edge.edge_id] = edge

    def neighbors(self, node_id: str) -> Tuple[Node, ...]:
        found: List[Node] = []
        for edge in self.edges.values():
            if node_id in edge.node_ids:
                for other in edge.node_ids:
                    if other != node_id and other in self.nodes:
                        found.append(self.nodes[other])
        unique = {node.node_id: node for node in found}
        return tuple(unique.values())

    def answer_auto_questions(self) -> Dict[str, Tuple[str, ...]]:
        courses = [n for n in self.nodes.values() if n.kind == "course"]
        labs = [n for n in self.nodes.values() if n.kind == "lab"]
        prototypes = [n for n in self.nodes.values() if n.kind == "prototype"]
        partners = [n for n in self.nodes.values() if n.kind == "partner"]
        return {
            "courses_that_can_become_labs": tuple(course.label for course in courses),
            "labs_that_can_become_articles": tuple(lab.label for lab in labs),
            "prototypes_partner_ready": tuple(proto.label for proto in prototypes if partners),
            "graph_holes": self.detect_holes(),
        }

    def detect_holes(self) -> Tuple[str, ...]:
        holes: List[str] = []
        kinds = {node.kind for node in self.nodes.values()}
        for required in ("professor", "course", "lab", "project", "prototype", "partner"):
            if required not in kinds:
                holes.append(f"missing_{required}_node")
        if not self.edges:
            holes.append("missing_hyperedges")
        return tuple(holes)


def demo_professor_graph() -> ProfessorGraph:
    graph = ProfessorGraph()
    graph.add_node(Node("p1", "professor", "Professor demo"))
    graph.add_node(Node("c1", "course", "Signal processing"))
    graph.add_node(Node("l1", "lab", "FFT uncertainty lab"))
    graph.add_node(Node("pr1", "project", "Photonic sensor project"))
    graph.add_node(Node("proto1", "prototype", "Low-cost photonic sensor"))
    graph.add_node(Node("partner1", "partner", "Industry partner demo"))
    graph.add_edge(HyperEdge("e1", "teaches_to_lab", ("p1", "c1", "l1"), 0.9))
    graph.add_edge(HyperEdge("e2", "lab_to_project_to_prototype", ("l1", "pr1", "proto1"), 0.8))
    graph.add_edge(HyperEdge("e3", "prototype_to_partner", ("proto1", "partner1"), 0.7))
    return graph
