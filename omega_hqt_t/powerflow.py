from __future__ import annotations
import math
from collections import deque
from .hashutil import sha256
from .models import Corridor, FlowResult, RegionState

def _components(nodes: list[str], corridors: list[Corridor]) -> list[list[str]]:
    adj={n:set() for n in nodes}
    for c in corridors:
        if c.source in adj and c.target in adj:
            adj[c.source].add(c.target); adj[c.target].add(c.source)
    seen=set(); comps=[]
    for node in nodes:
        if node in seen: continue
        q=deque([node]); seen.add(node); comp=[]
        while q:
            cur=q.popleft(); comp.append(cur)
            for nxt in sorted(adj[cur]):
                if nxt not in seen: seen.add(nxt); q.append(nxt)
        comps.append(comp)
    return comps

def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    n=len(b); aug=[row[:] + [b[i]] for i,row in enumerate(a)]
    for col in range(n):
        pivot=max(range(col,n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-12: raise ValueError("singular matrix")
        aug[col],aug[pivot]=aug[pivot],aug[col]
        scale=aug[col][col]; aug[col]=[x/scale for x in aug[col]]
        for row in range(n):
            if row==col: continue
            factor=aug[row][col]
            if factor: aug[row]=[aug[row][j]-factor*aug[col][j] for j in range(n+1)]
    return [aug[i][-1] for i in range(n)]

def run_dc_power_flow(regions: dict[str, RegionState], corridors: tuple[Corridor,...], *, unavailable: set[str] | None=None, demand_multiplier: float=1.0, generation_multiplier: float=1.0, outage_duration_h: float=1.0) -> FlowResult:
    unavailable=unavailable or set(); active=[c for c in corridors if c.corridor_id not in unavailable]
    nodes=sorted(regions); angles={n:0.0 for n in nodes}; flows={}; overloads={}; disconnected=[]
    served_total=0.0; unserved=0.0; residual=0.0
    for comp in _components(nodes, active):
        comp_corr=[c for c in active if c.source in comp and c.target in comp]
        demand={n:regions[n].demand_mw*demand_multiplier for n in comp}
        generation={n:regions[n].generation_mw*generation_multiplier for n in comp}
        total_d=sum(demand.values()); total_g=sum(generation.values()); served=min(total_d,total_g)
        served_total+=served; unserved+=(total_d-served)*outage_duration_h
        if not comp_corr:
            disconnected.extend(comp); continue
        scale=(served/total_d) if total_d else 1.0
        injections={n:generation[n]-demand[n]*scale for n in comp}
        slack=max(comp,key=lambda n:generation[n])
        injections[slack]-=sum(injections.values())
        unknown=[n for n in sorted(comp) if n!=slack]; idx={n:i for i,n in enumerate(unknown)}
        bmat=[[0.0]*len(unknown) for _ in unknown]; rhs=[injections[n] for n in unknown]
        for c in comp_corr:
            susceptance=1.0/c.reactance_pu
            a,b=c.source,c.target
            if a!=slack: bmat[idx[a]][idx[a]]+=susceptance
            if b!=slack: bmat[idx[b]][idx[b]]+=susceptance
            if a!=slack and b!=slack:
                bmat[idx[a]][idx[b]]-=susceptance; bmat[idx[b]][idx[a]]-=susceptance
        try: solved=_solve(bmat,rhs)
        except ValueError:
            disconnected.extend(comp); unserved+=served*outage_duration_h; served_total-=served; continue
        for n,val in zip(unknown,solved): angles[n]=val
        for c in comp_corr:
            flow=(angles[c.source]-angles[c.target])/c.reactance_pu
            flows[c.corridor_id]=flow
            if abs(flow)>c.capacity_mw: overloads[c.corridor_id]=abs(flow)-c.capacity_mw
        residual+=abs(sum(injections.values()))
    for c in corridors:
        flows.setdefault(c.corridor_id,0.0)
    finite=all(math.isfinite(x) for x in [*angles.values(),*flows.values(),served_total,unserved])
    losses=sum(abs(v) for v in flows.values())*0.0015
    payload={"angles":angles,"flows":flows,"overloads":overloads,"disconnected":sorted(set(disconnected)),"served":served_total,"unserved":unserved,"losses":losses,"residual":residual,"finite":finite}
    return FlowResult(angles,flows,overloads,tuple(sorted(set(disconnected))),served_total,unserved,losses,residual,finite,sha256(payload))
