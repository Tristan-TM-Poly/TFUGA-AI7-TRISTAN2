from __future__ import annotations
from dataclasses import dataclass
from .general_network import BalanceNode, DirectedArc, min_cost_general_flow
from .temporal_network import TemporalArc, TemporalBalance, solve_time_expanded_flow

@dataclass(frozen=True, slots=True)
class SolverCrosscheckReport:
    internal_flow: float
    external_flow: float
    internal_cost: float
    external_cost: float
    flow_agreement: bool
    cost_agreement: bool
    external_solver: str = "scipy.optimize.linprog(method=highs)"
    claim_boundary: str = "independent_software_crosscheck_not_formal_proof"

def scipy_available()->bool:
    try:
        import scipy
    except ImportError:
        return False
    return True

def _scipy_lexicographic_flow(nodes: tuple[BalanceNode,...], arcs: tuple[DirectedArc,...]) -> tuple[float,float]:
    try:
        from scipy.optimize import linprog
    except ImportError as exc:
        raise RuntimeError("SciPy evidence extra is required for external solver cross-check") from exc
    ids=[n.node_id for n in nodes]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate node_id")
    idx={node_id:i for i,node_id in enumerate(ids)}
    for a in arcs:
        if a.source_id not in idx or a.target_id not in idx: raise KeyError("arc endpoint is not a declared node")
    supplies=[n for n in nodes if n.net_supply>0]
    demands=[n for n in nodes if n.net_supply<0]
    na=len(arcs); ns=len(supplies); nd=len(demands); nvar=na+ns+nd
    Aeq=[]; beq=[]
    for n in nodes:
        row=[0.0]*nvar
        for j,a in enumerate(arcs):
            if a.source_id==n.node_id: row[j]+=1.0
            if a.target_id==n.node_id: row[j]-=1.0
        for j,s in enumerate(supplies):
            if s.node_id==n.node_id: row[na+j]-=1.0
        for j,d in enumerate(demands):
            if d.node_id==n.node_id: row[na+ns+j]+=1.0
        Aeq.append(row); beq.append(0.0)
    bounds=[(0.0,a.capacity) for a in arcs]+[(0.0,s.net_supply) for s in supplies]+[(0.0,-d.net_supply) for d in demands]
    c1=[0.0]*(na+ns)+[-1.0]*nd
    r1=linprog(c1,A_eq=Aeq,b_eq=beq,bounds=bounds,method="highs")
    if not r1.success: raise RuntimeError(f"external max-flow LP failed: {r1.message}")
    max_flow=float(sum(r1.x[na+ns:]))
    flow_row=[0.0]*(na+ns)+[1.0]*nd
    c2=[a.unit_cost for a in arcs]+[0.0]*(ns+nd)
    r2=linprog(c2,A_eq=Aeq+[flow_row],b_eq=beq+[max_flow],bounds=bounds,method="highs")
    if not r2.success: raise RuntimeError(f"external min-cost LP failed: {r2.message}")
    return max_flow,float(r2.fun)

def _report(internal_flow:float, internal_cost:float, external_flow:float, external_cost:float, tolerance:float)->SolverCrosscheckReport:
    return SolverCrosscheckReport(
        internal_flow,external_flow,internal_cost,external_cost,
        abs(internal_flow-external_flow)<=tolerance,
        abs(internal_cost-external_cost)<=tolerance,
    )

def crosscheck_general_flow(nodes: tuple[BalanceNode,...], arcs: tuple[DirectedArc,...], *, tolerance:float=1e-8)->SolverCrosscheckReport:
    internal=min_cost_general_flow(nodes,arcs)
    ef,ec=_scipy_lexicographic_flow(nodes,arcs)
    return _report(internal.total_flow,internal.total_cost,ef,ec,tolerance)

def _expand_temporal_problem(
    balances:tuple[TemporalBalance,...],
    arcs:tuple[TemporalArc,...],
    *,
    holdover_nodes:tuple[str,...]=(),
    periods:tuple[int,...]=(),
    holdover_capacity:float=1e18,
    holdover_unit_cost:float=0.0,
)->tuple[tuple[BalanceNode,...],tuple[DirectedArc,...]]:
    def tid(node_id:str,period:int)->str: return f"{node_id}@{period}"
    keys={(b.node_id,b.period) for b in balances}
    for a in arcs:
        keys.add((a.source_id,a.depart_period)); keys.add((a.target_id,a.arrive_period))
    for node_id in holdover_nodes:
        for period in periods: keys.add((node_id,period))
    net={}
    for b in balances: net[(b.node_id,b.period)]=net.get((b.node_id,b.period),0.0)+b.net_supply
    nodes=tuple(BalanceNode(tid(n,p),net.get((n,p),0.0)) for n,p in sorted(keys,key=lambda z:(z[1],z[0])))
    directed=[DirectedArc(tid(a.source_id,a.depart_period),tid(a.target_id,a.arrive_period),a.capacity,a.unit_cost,a.label) for a in arcs]
    ordered=sorted(set(periods))
    for node_id in holdover_nodes:
        for first,second in zip(ordered,ordered[1:]):
            directed.append(DirectedArc(tid(node_id,first),tid(node_id,second),holdover_capacity,holdover_unit_cost,"holdover"))
    return nodes,tuple(directed)

def crosscheck_time_expanded_flow(
    balances:tuple[TemporalBalance,...],
    arcs:tuple[TemporalArc,...],
    *,
    holdover_nodes:tuple[str,...]=(),
    periods:tuple[int,...]=(),
    holdover_capacity:float=1e18,
    holdover_unit_cost:float=0.0,
    tolerance:float=1e-8,
)->SolverCrosscheckReport:
    internal=solve_time_expanded_flow(
        balances,arcs,holdover_nodes=holdover_nodes,periods=periods,
        holdover_capacity=holdover_capacity,holdover_unit_cost=holdover_unit_cost,
    )
    nodes,directed=_expand_temporal_problem(
        balances,arcs,holdover_nodes=holdover_nodes,periods=periods,
        holdover_capacity=holdover_capacity,holdover_unit_cost=holdover_unit_cost,
    )
    ef,ec=_scipy_lexicographic_flow(nodes,directed)
    return _report(internal.total_flow,internal.total_cost,ef,ec,tolerance)
