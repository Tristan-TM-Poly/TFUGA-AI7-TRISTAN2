"""Deterministic HGFMnD² graph export for Ω-NARUTO proposals and OAK results."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from html import escape
from typing import Any, Iterable

from .core import AgentProposal, OAKMergeResult


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    kind: str
    label: str
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    source: str
    target: str
    relation: str
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class HGFMGraph:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "omega_naruto_hgfmn.graph.v1",
            "directed": True,
            "nodes": [
                {
                    "id": node.node_id,
                    "kind": node.kind,
                    "label": node.label,
                    "attributes": dict(node.attributes),
                }
                for node in self.nodes
            ],
            "edges": [
                {
                    "id": edge.edge_id,
                    "source": edge.source,
                    "target": edge.target,
                    "relation": edge.relation,
                    "attributes": dict(edge.attributes),
                }
                for edge in self.edges
            ],
        }

    def to_graphml(self) -> str:
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '  <key id="kind" for="node" attr.name="kind" attr.type="string"/>',
            '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
            '  <key id="relation" for="edge" attr.name="relation" attr.type="string"/>',
            '  <graph id="omega-naruto-hgfmn" edgedefault="directed">',
        ]
        for node in self.nodes:
            lines.extend(
                [
                    f'    <node id="{escape(node.node_id, quote=True)}">',
                    f'      <data key="kind">{escape(node.kind)}</data>',
                    f'      <data key="label">{escape(node.label)}</data>',
                    "    </node>",
                ]
            )
        for edge in self.edges:
            lines.extend(
                [
                    (
                        f'    <edge id="{escape(edge.edge_id, quote=True)}" '
                        f'source="{escape(edge.source, quote=True)}" '
                        f'target="{escape(edge.target, quote=True)}">'
                    ),
                    f'      <data key="relation">{escape(edge.relation)}</data>',
                    "    </edge>",
                ]
            )
        lines.extend(["  </graph>", "</graphml>"])
        return "\n".join(lines) + "\n"


def _stable_id(prefix: str, value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _edge_id(source: str, relation: str, target: str) -> str:
    return _stable_id("edge", f"{source}|{relation}|{target}")


def build_hgfmn_graph(
    proposals: Iterable[AgentProposal],
    result: OAKMergeResult,
) -> HGFMGraph:
    """Build a deterministic evidence/provenance/contradiction graph.

    The export represents local software state. It does not certify the truth of
    a proposal, evidence item, provenance marker, or selected conclusion.
    """

    items = tuple(sorted(proposals, key=lambda item: item.proposal_id))
    nodes: dict[str, GraphNode] = {}
    edges: dict[str, GraphEdge] = {}

    decision_id = "oak:decision"
    nodes[decision_id] = GraphNode(
        decision_id,
        "oak_decision",
        "OAKMerge local decision",
        (("non_claim", "selection is not certification"),),
    )

    for proposal in items:
        proposal_id = f"proposal:{proposal.proposal_id}"
        nodes[proposal_id] = GraphNode(
            proposal_id,
            "proposal",
            proposal.conclusion,
            (
                ("agent_id", proposal.agent_id),
                ("status", proposal.status.name),
                ("confidence", f"{proposal.confidence:.6f}"),
                ("uncertainty", f"{proposal.uncertainty:.6f}"),
            ),
        )

        hypothesis_id = _stable_id("hypothesis", proposal.hypothesis)
        nodes.setdefault(
            hypothesis_id,
            GraphNode(hypothesis_id, "hypothesis", proposal.hypothesis),
        )
        relation = "tests_hypothesis"
        edge = GraphEdge(
            _edge_id(proposal_id, relation, hypothesis_id),
            proposal_id,
            hypothesis_id,
            relation,
        )
        edges[edge.edge_id] = edge

        for evidence in sorted(set(proposal.evidence)):
            evidence_id = _stable_id("evidence", evidence)
            nodes.setdefault(
                evidence_id,
                GraphNode(evidence_id, "evidence", evidence),
            )
            relation = "supported_by"
            edge = GraphEdge(
                _edge_id(proposal_id, relation, evidence_id),
                proposal_id,
                evidence_id,
                relation,
            )
            edges[edge.edge_id] = edge

        for provenance in sorted(set(proposal.provenance)):
            provenance_id = _stable_id("provenance", provenance)
            nodes.setdefault(
                provenance_id,
                GraphNode(provenance_id, "provenance", provenance),
            )
            relation = "derived_from"
            edge = GraphEdge(
                _edge_id(proposal_id, relation, provenance_id),
                proposal_id,
                provenance_id,
                relation,
            )
            edges[edge.edge_id] = edge

    accepted_id = (
        f"proposal:{result.accepted.proposal_id}"
        if result.accepted is not None
        else None
    )
    if accepted_id is not None:
        edge = GraphEdge(
            _edge_id(decision_id, "locally_selects", accepted_id),
            decision_id,
            accepted_id,
            "locally_selects",
        )
        edges[edge.edge_id] = edge

    for rejected in sorted(result.rejected, key=lambda item: item.proposal_id):
        target = f"proposal:{rejected.proposal_id}"
        if target not in nodes:
            continue
        edge = GraphEdge(
            _edge_id(decision_id, "retains_in_mminus", target),
            decision_id,
            target,
            "retains_in_mminus",
            (("reason", rejected.reason),),
        )
        edges[edge.edge_id] = edge

    for left, right in sorted(result.contradictions):
        source = f"proposal:{left}"
        target = f"proposal:{right}"
        if source not in nodes or target not in nodes:
            continue
        edge = GraphEdge(
            _edge_id(source, "contradicts", target),
            source,
            target,
            "contradicts",
        )
        edges[edge.edge_id] = edge

    return HGFMGraph(
        nodes=tuple(nodes[key] for key in sorted(nodes)),
        edges=tuple(edges[key] for key in sorted(edges)),
    )
