from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True, slots=True)
class Commodity:
    commodity_id: str
    source_id: str
    sink_id: str
    max_quantity: float
    def __post_init__(self):
        if not self.commodity_id or not self.source_id or not self.sink_id: raise ValueError("commodity ids/endpoints required")
        if self.source_id==self.sink_id: raise ValueError("source and sink must differ")
        if self.max_quantity<0 or not math.isfinite(self.max_quantity): raise ValueError("max_quantity must be finite and non-negative")

@dataclass(frozen=True, slots=True)
class SharedArc:
    arc_id: str
    source_id: str
    target_id: str
    capacity: float
    unit_cost: float
    def __post_init__(self):
        if not self.arc_id or not self.source_id or not self.target_id: raise ValueError("arc id/endpoints required")
        if self.capacity<0 or not math.isfinite(self.capacity): raise ValueError("capacity must be finite and non-negative")
        if self.unit_cost<0 or not math.isfinite(self.unit_cost): raise ValueError("unit_cost must be finite and non-negative")

@dataclass(frozen=True, slots=True)
class CommodityAllocation:
    commodity_id: str
    arc_id: str
    source_id: str
    target_id: str
    quantity: float
    unit_cost: float

@dataclass(frozen=True, slots=True)
class MultiCommodityResult:
    total_flow: float
    total_cost: float
    delivered: tuple[tuple[str,float],...]
    allocations: tuple[CommodityAllocation,...]
    optimality_certified: bool
    solver: str = "scipy.optimize.linprog(method=highs)"
    claim_boundary: str = "fractional_multi_commodity_lp_with_declared_shared_arc_capacities_only"

def solve_fractional_multi_commodity(commodities:tuple[Commodity,...], arcs:tuple[SharedArc,...], *, tolerance:float=1e-9)->MultiCommodityResult:
    try:
        from scipy.optimize import linprog
    except ImportError as exc:
        raise RuntimeError("SciPy evidence extra is required for multi-commodity LP") from exc
    cids=[c.commodity_id for c in commodities]
    aids=[a.arc_id for a in arcs]
    if len(cids)!=len(set(cids)): raise ValueError("duplicate commodity_id")
    if len(aids)!=len(set(aids)): raise ValueError("duplicate arc_id")
    nodes=sorted({x for a in arcs for x in (a.source_id,a.target_id)} | {x for c in commodities for x in (c.source_id,c.sink_id)})
    K=len(commodities); A=len(arcs); nflow=K*A; nvar=nflow+K
    def vid(k,a): return k*A+a
    qoff=nflow
    Aeq=[]; beq=[]
    for k,c in enumerate(commodities):
        for node in nodes:
            row=[0.0]*nvar
            for ai,a in enumerate(arcs):
                if a.source_id==node: row[vid(k,ai)]+=1.0
                if a.target_id==node: row[vid(k,ai)]-=1.0
            if node==c.source_id: row[qoff+k]-=1.0
            if node==c.sink_id: row[qoff+k]+=1.0
            Aeq.append(row); beq.append(0.0)
    Aub=[]; bub=[]
    for ai,a in enumerate(arcs):
        row=[0.0]*nvar
        for k in range(K): row[vid(k,ai)]=1.0
        Aub.append(row); bub.append(a.capacity)
    bounds=[(0.0,None)]*nflow + [(0.0,c.max_quantity) for c in commodities]
    c1=[0.0]*nflow+[-1.0]*K
    r1=linprog(c1,A_ub=Aub,b_ub=bub,A_eq=Aeq,b_eq=beq,bounds=bounds,method="highs")
    if not r1.success: raise RuntimeError(f"multi-commodity max-flow LP failed: {r1.message}")
    max_flow=float(sum(r1.x[qoff:]))
    flow_row=[0.0]*nflow+[1.0]*K
    c2=[]
    for _k in range(K): c2.extend(a.unit_cost for a in arcs)
    c2 += [0.0]*K
    r2=linprog(c2,A_ub=Aub,b_ub=bub,A_eq=Aeq+[flow_row],b_eq=beq+[max_flow],bounds=bounds,method="highs")
    if not r2.success: raise RuntimeError(f"multi-commodity min-cost LP failed: {r2.message}")
    allocations=[]
    for k,c in enumerate(commodities):
        for ai,a in enumerate(arcs):
            q=float(r2.x[vid(k,ai)])
            if q>tolerance: allocations.append(CommodityAllocation(c.commodity_id,a.arc_id,a.source_id,a.target_id,q,a.unit_cost))
    allocations.sort(key=lambda z:(z.commodity_id,z.arc_id))
    delivered=tuple(sorted(((c.commodity_id,float(r2.x[qoff+k])) for k,c in enumerate(commodities))))
    return MultiCommodityResult(max_flow,float(r2.fun),delivered,tuple(allocations),True)
