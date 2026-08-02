from __future__ import annotations
from dataclasses import dataclass,asdict
from collections import defaultdict,deque
from typing import Any
from .models import CandidateCell
@dataclass(frozen=True)
class HyperNode: node_id:str; kind:str; label:str; attributes:dict[str,Any]
@dataclass(frozen=True)
class HyperEdge:
    edge_id:str; relation:str; members:tuple[str,...]; attributes:dict[str,Any]
    def __post_init__(self):
        if len(self.members)<2 or len(set(self.members))!=len(self.members): raise ValueError('hyperedge requires unique members')
class SolidHypergraph:
    def __init__(self): self.nodes={}; self.edges={}; self.incidence=defaultdict(set)
    def add_node(self,node):
        old=self.nodes.get(node.node_id)
        if old is not None and old!=node: raise ValueError(f'conflicting node {node.node_id}')
        self.nodes[node.node_id]=node
    def add_edge(self,edge):
        if edge.edge_id in self.edges and self.edges[edge.edge_id]!=edge: raise ValueError(f'conflicting edge {edge.edge_id}')
        missing=[m for m in edge.members if m not in self.nodes]
        if missing: raise KeyError(f'missing nodes: {missing}')
        self.edges[edge.edge_id]=edge
        for member in edge.members:self.incidence[member].add(edge.edge_id)
    def neighbors(self,node_id):
        out=set()
        for edge_id in self.incidence[node_id]: out.update(self.edges[edge_id].members)
        out.discard(node_id); return out
    def connected_components(self):
        remaining=set(self.nodes); comps=[]
        while remaining:
            root=next(iter(remaining)); seen={root}; queue=deque([root])
            while queue:
                node=queue.popleft()
                for other in self.neighbors(node):
                    if other not in seen: seen.add(other); queue.append(other)
            remaining-=seen; comps.append(seen)
        return comps
    def validate(self):
        missing=[]
        for edge in self.edges.values(): missing.extend(m for m in edge.members if m not in self.nodes)
        return {'nodes':len(self.nodes),'hyperedges':len(self.edges),'missing_members':sorted(set(missing)),'components':len(self.connected_components()) if self.nodes else 0,'valid':not missing}
    def to_dict(self): return {'nodes':[asdict(self.nodes[k]) for k in sorted(self.nodes)],'hyperedges':[asdict(self.edges[k]) for k in sorted(self.edges)]}
    def to_graphml(self):
        esc=lambda s:str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')
        lines=['<?xml version="1.0" encoding="UTF-8"?>','<graphml xmlns="http://graphml.graphdrawing.org/xmlns">','<graph id="solid-hypergraph" edgedefault="undirected">']
        for node in sorted(self.nodes.values(),key=lambda x:x.node_id): lines.append(f'<node id="{esc(node.node_id)}"><data key="kind">{esc(node.kind)}</data><data key="label">{esc(node.label)}</data></node>')
        for edge in sorted(self.edges.values(),key=lambda x:x.edge_id):
            en=f'hyperedge::{edge.edge_id}'; lines.append(f'<node id="{esc(en)}"><data key="kind">hyperedge</data><data key="label">{esc(edge.relation)}</data></node>')
            for i,member in enumerate(edge.members): lines.append(f'<edge id="{esc(edge.edge_id)}::{i}" source="{esc(en)}" target="{esc(member)}"/>')
        return '\n'.join(lines+['</graph>','</graphml>'])+'\n'
def from_candidate(c:CandidateCell):
    graph=SolidHypergraph(); root=f'candidate::{c.candidate_id}'; graph.add_node(HyperNode(root,'candidate',c.candidate_id,{'fingerprint':c.fingerprint})); members=[root]
    for kind,ident,label in (('world',c.world_id,c.world_name),('architecture',c.architecture_id,c.architecture_name),('defect',c.defect_profile_id,c.defect_profile_id),('process',c.process_profile_id,c.process_profile_id),('environment',c.environment_profile_id,c.environment_profile_id)):
        node_id=f'{kind}::{ident}'; graph.add_node(HyperNode(node_id,kind,label,{})); members.append(node_id)
    graph.add_edge(HyperEdge(f'context::{c.logical_index}','candidate_context',tuple(members),{'status':c.epistemic_status.value}))
    for mechanism_id in c.mechanism_ids:
        node_id=f'mechanism::{mechanism_id}'; graph.add_node(HyperNode(node_id,'mechanism',mechanism_id,{})); graph.add_edge(HyperEdge(f'mechanism-link::{c.logical_index}::{mechanism_id}','candidate_mechanism',(root,node_id),{'requires_validation':True}))
    return graph
