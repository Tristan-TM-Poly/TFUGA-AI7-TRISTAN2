from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Iterable
from .hashutil import sha256
from .models import Evidence, Hyperedge, Node

@dataclass
class EnergyHypergraph:
    graph_id: str
    nodes: dict[str, Node] = field(default_factory=dict)
    hyperedges: dict[str, Hyperedge] = field(default_factory=dict)
    evidence: dict[str, Evidence] = field(default_factory=dict)

    def add_evidence(self, item: Evidence) -> None:
        if item.evidence_id in self.evidence and self.evidence[item.evidence_id] != item:
            raise ValueError(f"conflicting evidence {item.evidence_id}")
        self.evidence[item.evidence_id]=item

    def add_node(self, node: Node) -> None:
        if node.node_id in self.nodes and self.nodes[node.node_id] != node:
            raise ValueError(f"conflicting node {node.node_id}")
        self.nodes[node.node_id]=node

    def add_hyperedge(self, edge: Hyperedge) -> None:
        all_ids=set(edge.sources) | set(edge.targets)
        missing=all_ids-set(self.nodes)
        if missing: raise ValueError(f"edge {edge.edge_id} references missing nodes: {sorted(missing)}")
        if not 0.0 <= edge.confidence <= 1.0: raise ValueError("confidence must be within [0,1]")
        self.hyperedges[edge.edge_id]=edge

    def validate(self) -> list[str]:
        errors=[]
        for node in self.nodes.values():
            missing=set(node.evidence_ids)-set(self.evidence)
            if missing: errors.append(f"node:{node.node_id}:missing-evidence:{sorted(missing)}")
        for edge in self.hyperedges.values():
            missing_nodes=(set(edge.sources)|set(edge.targets))-set(self.nodes)
            missing_evidence=set(edge.evidence_ids)-set(self.evidence)
            if missing_nodes: errors.append(f"edge:{edge.edge_id}:missing-nodes:{sorted(missing_nodes)}")
            if missing_evidence: errors.append(f"edge:{edge.edge_id}:missing-evidence:{sorted(missing_evidence)}")
        return errors

    def projection(self, *, levels: Iterable[str] | None = None, kinds: Iterable[str] | None = None) -> "EnergyHypergraph":
        levels=set(levels or []); kinds=set(kinds or [])
        selected={nid:n for nid,n in self.nodes.items() if (not levels or n.level in levels) and (not kinds or n.kind in kinds)}
        edges={eid:e for eid,e in self.hyperedges.items() if (set(e.sources)|set(e.targets)).issubset(selected)}
        evidence_ids={x for n in selected.values() for x in n.evidence_ids} | {x for e in edges.values() for x in e.evidence_ids}
        return EnergyHypergraph(self.graph_id+":projection", selected, edges, {k:v for k,v in self.evidence.items() if k in evidence_ids})

    def adjacency(self) -> dict[str, set[str]]:
        result={nid:set() for nid in self.nodes}
        for edge in self.hyperedges.values():
            members=list(dict.fromkeys([*edge.sources,*edge.targets]))
            for a in members:
                result[a].update(b for b in members if b != a)
        return result

    def to_dict(self) -> dict[str, Any]:
        payload={
            "graph_id": self.graph_id,
            "nodes": [self.nodes[k].to_dict() for k in sorted(self.nodes)],
            "hyperedges": [self.hyperedges[k].to_dict() for k in sorted(self.hyperedges)],
            "evidence": [self.evidence[k].to_dict() for k in sorted(self.evidence)],
            "validation_errors": self.validate(),
        }
        payload["evidence_hash"]=sha256(payload)
        return payload
