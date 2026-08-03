"""Graph algorithms for the canonical Transformation IR."""
from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass, field
import math, re
from typing import Iterable
from .contracts import IREdge, IRNode, ObjectKind, RelationKind, TransformationIR, stable_id

_TOKEN_RE=re.compile(r"[A-Za-z0-9_+.-]+")
DEFAULT_ALIASES={"claim":{"claim_atom","claim_candidate","assertion"},"evidence":{"evidence_record","evidence_bundle","proof_artifact","receipt"},"repository":{"repo","repository_snapshot","repotwin"},"pull_request":{"pr","pr_gene","draft_pull_request"},"knowledge_graph":{"hypergraph","claim_graph","evidence_graph","theory_graph"},"experiment":{"test_plan","causal_experiment","oakbench"},"portfolio":{"prototype_portfolio","work_portfolio","selection_plan"},"intent":{"intention","intent_contract","objective_contract"},"measurement":{"metric","observed_result","benchmark_result"}}

def normalize_type(value:str)->str: return ":".join(token.lower() for token in _TOKEN_RE.findall(value))
def _alias_groups(aliases=None):
    groups={}
    for canonical,values in (aliases or DEFAULT_ALIASES).items():
        normalized=normalize_type(canonical); groups[normalized]=normalized
        for value in values: groups[normalize_type(value)]=normalized
    return groups
def canonical_type(value:str,aliases=None)->str:
    normalized=normalize_type(value); return _alias_groups(aliases).get(normalized,normalized)
def type_similarity(left:str,right:str,aliases=None)->float:
    left_norm,right_norm=canonical_type(left,aliases),canonical_type(right,aliases)
    if not left_norm or not right_norm:return 0.0
    if left_norm==right_norm:return 1.0
    lt,rt=set(left_norm.split(":")),set(right_norm.split(":")); union=len(lt|rt)
    if not union:return 0.0
    score=len(lt&rt)/union
    if left_norm in right_norm or right_norm in left_norm:score=max(score,0.65)
    return round(score,6)

@dataclass(slots=True)
class BridgeCandidate:
    id:str; provider_id:str; consumer_id:str; provider_types:list[str]; consumer_types:list[str]; mappings:dict[str,str]; score:float; exact_matches:int; alias_matches:int; lossy_matches:int; required_interface:str; preserved_invariants:list[str]=field(default_factory=list); declared_losses:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list)
    def to_dict(self):return {"id":self.id,"provider_id":self.provider_id,"consumer_id":self.consumer_id,"provider_types":self.provider_types,"consumer_types":self.consumer_types,"mappings":dict(sorted(self.mappings.items())),"score":self.score,"exact_matches":self.exact_matches,"alias_matches":self.alias_matches,"lossy_matches":self.lossy_matches,"required_interface":self.required_interface,"preserved_invariants":sorted(set(self.preserved_invariants)),"declared_losses":sorted(set(self.declared_losses)),"warnings":sorted(set(self.warnings))}

class TransformationGraph:
    def __init__(self,ir:TransformationIR):
        self.ir=ir; self.nodes={n.id:n for n in ir.nodes}; self.outgoing=defaultdict(list); self.incoming=defaultdict(list)
        for edge in ir.edges:self.outgoing[edge.source].append(edge);self.incoming[edge.target].append(edge)
        for edges in self.outgoing.values():edges.sort(key=lambda e:(e.relation.value,e.target,e.id))
        for edges in self.incoming.values():edges.sort(key=lambda e:(e.relation.value,e.source,e.id))
    def neighbors(self,node_id,*,relations=None,reverse=False):
        edge_map=self.incoming if reverse else self.outgoing; result=[]
        for edge in edge_map.get(node_id,[]):
            if relations is not None and edge.relation not in relations:continue
            result.append(edge.source if reverse else edge.target)
        return sorted(set(result))
    def impact_closure(self,changed_ids,*,relations=None,max_depth=16):
        allowed=relations or {RelationKind.PRODUCES,RelationKind.SUPPORTS,RelationKind.DEPENDS_ON,RelationKind.IMPLEMENTS,RelationKind.TESTS,RelationKind.RESOLVES,RelationKind.ADAPTS_TO}
        queue=deque((n,0) for n in sorted(set(changed_ids)) if n in self.nodes);seen={n for n,_ in queue}
        while queue:
            node,depth=queue.popleft()
            if depth>=max_depth:continue
            candidates=self.neighbors(node,relations=allowed)+self.neighbors(node,relations=allowed,reverse=True)
            for neighbor in sorted(set(candidates)):
                if neighbor not in seen:seen.add(neighbor);queue.append((neighbor,depth+1))
        return sorted(seen)
    def closure_paths(self,source,target,*,max_depth=8,relations=None,max_paths=64):
        if source not in self.nodes or target not in self.nodes:return []
        if source==target:return [[source]]
        paths=[];queue=deque([[source]])
        while queue and len(paths)<max_paths:
            path=queue.popleft()
            if len(path)-1>=max_depth:continue
            for neighbor in self.neighbors(path[-1],relations=relations):
                if neighbor in path:continue
                candidate=[*path,neighbor]
                if neighbor==target:paths.append(candidate)
                else:queue.append(candidate)
        return sorted(paths,key=lambda item:(len(item),item))
    def strongly_connected_components(self,relations=None):
        allowed=relations or {RelationKind.DEPENDS_ON,RelationKind.PRODUCES,RelationKind.IMPLEMENTS};index=0;stack=[];on_stack=set();indices={};lowlinks={};components=[]
        def visit(node):
            nonlocal index
            indices[node]=lowlinks[node]=index;index+=1;stack.append(node);on_stack.add(node)
            for neighbor in self.neighbors(node,relations=allowed):
                if neighbor not in indices:visit(neighbor);lowlinks[node]=min(lowlinks[node],lowlinks[neighbor])
                elif neighbor in on_stack:lowlinks[node]=min(lowlinks[node],indices[neighbor])
            if lowlinks[node]==indices[node]:
                component=[]
                while True:
                    member=stack.pop();on_stack.remove(member);component.append(member)
                    if member==node:break
                components.append(sorted(component))
        for node in sorted(self.nodes):
            if node not in indices:visit(node)
        return sorted(components,key=lambda item:(len(item),item),reverse=True)
    def dependency_cycles(self):
        cycles=[]
        for component in self.strongly_connected_components({RelationKind.DEPENDS_ON}):
            if len(component)>1 or component[0] in self.neighbors(component[0],relations={RelationKind.DEPENDS_ON}):cycles.append(component)
        return sorted(cycles)
    def coverage(self):
        total=len(self.nodes)
        if not total:return {"nodes":0,"typed_nodes":0,"evidenced_nodes":0,"provenanced_nodes":0,"typed_ratio":0.0,"evidence_ratio":0.0,"provenance_ratio":0.0}
        typed=sum(bool(n.input_types or n.output_types) for n in self.nodes.values());evidenced=sum(bool(n.evidence_refs) for n in self.nodes.values());provenanced=sum(bool(n.provenance) for n in self.nodes.values())
        return {"nodes":total,"typed_nodes":typed,"evidenced_nodes":evidenced,"provenanced_nodes":provenanced,"typed_ratio":round(typed/total,6),"evidence_ratio":round(evidenced/total,6),"provenance_ratio":round(provenanced/total,6)}
    def interface_entropy(self):
        counts=defaultdict(int)
        for node in self.nodes.values():
            for value in [*node.input_types,*node.output_types]:
                normalized=canonical_type(value)
                if normalized:counts[normalized]+=1
        total=sum(counts.values())
        if total<=1 or len(counts)<=1:return 0.0
        entropy=-sum((count/total)*math.log2(count/total) for count in counts.values());maximum=math.log2(len(counts))
        return round(entropy/maximum if maximum else 0.0,6)

def _provider_types(node):return [] if node.kind==ObjectKind.NEED else sorted(set(node.output_types))
def _consumer_types(node):return [] if node.kind==ObjectKind.CAPABILITY else sorted(set(node.input_types or node.output_types if node.kind==ObjectKind.NEED else node.input_types))

def discover_bridges(ir,*,aliases=None,threshold=0.45,max_results=250):
    if not 0<=threshold<=1:raise ValueError("threshold must be between 0 and 1")
    providers=[n for n in ir.nodes if _provider_types(n)];consumers=[n for n in ir.nodes if _consumer_types(n)];results=[];alias_groups=_alias_groups(aliases)
    for provider in sorted(providers,key=lambda n:n.id):
        for consumer in sorted(consumers,key=lambda n:n.id):
            if provider.id==consumer.id:continue
            pt,ct=_provider_types(provider),_consumer_types(consumer);mappings={};scores=[];exact=alias=lossy=0;used=set()
            for consumer_type in ct:
                ranked=sorted(((type_similarity(provider_type,consumer_type,aliases),provider_type) for provider_type in pt if provider_type not in used),key=lambda item:(-item[0],item[1]))
                if not ranked or ranked[0][0]<threshold:continue
                score,provider_type=ranked[0];mappings[provider_type]=consumer_type;scores.append(score);used.add(provider_type);left,right=normalize_type(provider_type),normalize_type(consumer_type)
                if left==right:exact+=1
                elif alias_groups.get(left,left)==alias_groups.get(right,right):alias+=1
                else:lossy+=1
            if not scores:continue
            coverage=len(scores)/max(1,len(ct));mean=sum(scores)/len(scores);score=max(0.0,min(1.0,0.6*mean+0.4*coverage-(provider.uncertainty+consumer.uncertainty)/4));losses=[];warnings=[]
            if lossy:losses.append("semantic_type_approximation");warnings.append("lossy_type_mapping_requires_human_review")
            if coverage<1:losses.append("partial_consumer_type_coverage")
            if not provider.evidence_refs:warnings.append("provider_capability_lacks_named_evidence")
            if provider.risk>=.8 or consumer.risk>=.8:warnings.append("critical_risk_requires_isolation")
            results.append(BridgeCandidate(stable_id("BRIDGE",provider.id,consumer.id,mappings),provider.id,consumer.id,pt,ct,mappings,round(score,6),exact,alias,lossy,f"adapter:{provider.id}->{consumer.id}",["provenance","authority","uncertainty","declared_losses"],losses,warnings))
    results.sort(key=lambda item:(-item.score,item.provider_id,item.consumer_id,item.id));return results[:max_results]

def materialize_bridge(ir,bridge):
    node=IRNode.build(ObjectKind.INTERFACE,bridge.required_interface,source_identity=bridge.id,input_types=sorted(bridge.mappings),output_types=sorted(bridge.mappings.values()),provenance=[bridge.provider_id,bridge.consumer_id],uncertainty=round(1.0-bridge.score,6),risk=.2 if not bridge.declared_losses else .5,metadata={"mappings":dict(sorted(bridge.mappings.items())),"preserved_invariants":bridge.preserved_invariants,"declared_losses":bridge.declared_losses,"warnings":bridge.warnings,"review_only":True})
    incoming=IREdge.build(bridge.provider_id,node.id,RelationKind.ADAPTS_TO,interface=node.name,preserved_invariants=bridge.preserved_invariants,declared_losses=bridge.declared_losses,confidence=bridge.score)
    outgoing=IREdge.build(node.id,bridge.consumer_id,RelationKind.RESOLVES,interface=node.name,preserved_invariants=bridge.preserved_invariants,declared_losses=bridge.declared_losses,confidence=bridge.score)
    return node,incoming,outgoing
