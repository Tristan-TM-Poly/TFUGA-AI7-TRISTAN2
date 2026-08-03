"""Hybrid hypergraph plus simplicial evidence closure."""
from __future__ import annotations
from collections import defaultdict, deque
from .combinatorics import proper_subsets
from .models import Hyperedge, canonical_components, stable_id


class SynergyComplex:
    def __init__(self) -> None:
        self.nodes: set[str]=set()
        self.edges: dict[tuple[str,...],Hyperedge]={}

    def add_edge(self, components, **kwargs) -> Hyperedge:
        items=canonical_components(components)
        if not items: raise ValueError("empty hyperedge is reserved for baseline")
        edge=Hyperedge(id=kwargs.pop("id",stable_id("HYP",items)),components=items,order=len(items),**kwargs)
        self.nodes.update(items); self.edges[items]=edge
        return edge

    def evidence_closure(self, components) -> dict[tuple[str,...],str]:
        items=canonical_components(components)
        return {subset:("observed" if subset in self.edges else "missing") for subset in proper_subsets(items,include_empty=False)}

    def missing_faces(self, components) -> list[tuple[str,...]]:
        return [face for face,status in self.evidence_closure(components).items() if status=="missing"]

    def incidence(self) -> dict[str,list[str]]:
        result=defaultdict(list)
        for edge in self.edges.values():
            for node in edge.components: result[node].append(edge.id)
        return {k:sorted(v) for k,v in sorted(result.items())}

    def projected_adjacency(self) -> dict[str,set[str]]:
        graph={node:set() for node in self.nodes}
        for edge in self.edges.values():
            for a in edge.components:
                graph[a].update(x for x in edge.components if x!=a)
        return graph

    def connected_components(self) -> list[tuple[str,...]]:
        graph=self.projected_adjacency(); seen=set(); output=[]
        for start in sorted(graph):
            if start in seen: continue
            queue=deque([start]); part=[]; seen.add(start)
            while queue:
                node=queue.popleft(); part.append(node)
                for nxt in sorted(graph[node]-seen): seen.add(nxt); queue.append(nxt)
            output.append(tuple(part))
        return output

    def to_dict(self) -> dict:
        return {"nodes":sorted(self.nodes),"hyperedges":[e.to_dict() for e in sorted(self.edges.values(),key=lambda x:(x.order,x.components))],
                "incidence":self.incidence(),"connected_components":[list(x) for x in self.connected_components()]}
