from __future__ import annotations
from collections import deque
from dataclasses import asdict, dataclass
from .hashutil import sha256
from .models import Corridor

@dataclass(frozen=True)
class TopologyAudit:
    node_count: int
    edge_count: int
    connected_components: tuple[tuple[str,...],...]
    articulation_regions: tuple[str,...]
    bridge_corridors: tuple[str,...]
    redundancy_index: float
    evidence_hash: str
    def to_dict(self): return asdict(self)

def _adjacency(nodes: set[str], corridors: tuple[Corridor,...], skipped_edge: str|None=None, skipped_node: str|None=None):
    adj={n:set() for n in nodes if n!=skipped_node}
    for c in corridors:
        if c.corridor_id==skipped_edge or c.source==skipped_node or c.target==skipped_node: continue
        if c.source in adj and c.target in adj:
            adj[c.source].add(c.target); adj[c.target].add(c.source)
    return adj

def _components(adj: dict[str,set[str]]) -> tuple[tuple[str,...],...]:
    seen=set(); comps=[]
    for start in sorted(adj):
        if start in seen: continue
        q=deque([start]); seen.add(start); comp=[]
        while q:
            cur=q.popleft(); comp.append(cur)
            for nxt in sorted(adj[cur]):
                if nxt not in seen: seen.add(nxt); q.append(nxt)
        comps.append(tuple(sorted(comp)))
    return tuple(comps)

def audit_topology(corridors: tuple[Corridor,...]) -> TopologyAudit:
    nodes={x for c in corridors for x in (c.source,c.target)}
    base=_components(_adjacency(nodes,corridors)); base_count=len(base)
    articulations=[]
    for node in sorted(nodes):
        if len(_components(_adjacency(nodes,corridors,skipped_node=node)))>base_count: articulations.append(node)
    bridges=[]
    for c in corridors:
        if len(_components(_adjacency(nodes,corridors,skipped_edge=c.corridor_id)))>base_count: bridges.append(c.corridor_id)
    cycle_surplus=max(0,len(corridors)-len(nodes)+base_count)
    redundancy=cycle_surplus/max(len(nodes),1)
    core={'node_count':len(nodes),'edge_count':len(corridors),'connected_components':base,'articulation_regions':tuple(articulations),'bridge_corridors':tuple(sorted(bridges)),'redundancy_index':redundancy}
    return TopologyAudit(**core,evidence_hash=sha256(core))

def corridor_criticality(corridors: tuple[Corridor,...]) -> dict[str,float]:
    audit=audit_topology(corridors); bridge=set(audit.bridge_corridors)
    values={}
    for c in corridors:
        values[c.corridor_id]=(2.0 if c.corridor_id in bridge else 1.0)*(1.0+c.climate_exposure)*(1.0+c.length_index/5.0)*c.capacity_mw
    maximum=max(values.values(),default=1.0)
    return {k:v/maximum for k,v in sorted(values.items())}
