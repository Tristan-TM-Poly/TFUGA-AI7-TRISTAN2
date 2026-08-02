"""Minimal deterministic HGFM representation for plasma systems."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
import hashlib, json

@dataclass(frozen=True)
class Node:
    node_id:str; kind:str; label:str; attributes:dict=field(default_factory=dict)
@dataclass(frozen=True)
class Hyperedge:
    edge_id:str; kind:str; sources:tuple[str,...]; targets:tuple[str,...]; attributes:dict=field(default_factory=dict)
@dataclass
class PlasmaHypergraph:
    nodes:dict[str,Node]=field(default_factory=dict); edges:dict[str,Hyperedge]=field(default_factory=dict)
    def add_node(self,node:Node)->None:
        if node.node_id in self.nodes and self.nodes[node.node_id]!=node: raise ValueError(f"node collision: {node.node_id}")
        self.nodes[node.node_id]=node
    def add_edge(self,edge:Hyperedge)->None:
        missing=[x for x in (*edge.sources,*edge.targets) if x not in self.nodes]
        if missing: raise ValueError(f"edge {edge.edge_id} references missing nodes: {missing}")
        if edge.edge_id in self.edges and self.edges[edge.edge_id]!=edge: raise ValueError(f"edge collision: {edge.edge_id}")
        self.edges[edge.edge_id]=edge
    def canonical_dict(self)->dict: return {"nodes":[asdict(self.nodes[k]) for k in sorted(self.nodes)],"hyperedges":[asdict(self.edges[k]) for k in sorted(self.edges)]}
    def fingerprint(self)->str: return hashlib.sha256(json.dumps(self.canonical_dict(),sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    def audit(self)->dict:
        referenced={x for e in self.edges.values() for x in (*e.sources,*e.targets)}; isolated=sorted(set(self.nodes)-referenced); kinds={}
        for n in self.nodes.values(): kinds[n.kind]=kinds.get(n.kind,0)+1
        return {"fingerprint":self.fingerprint(),"node_count":len(self.nodes),"edge_count":len(self.edges),"node_kinds":kinds,"isolated_nodes":isolated,"status":"passed" if not isolated else "review"}
