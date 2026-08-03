from __future__ import annotations
from dataclasses import replace
from .models import Corridor, Intervention, RegionState, Scenario

def catalog() -> tuple[Intervention,...]:
    return (
        Intervention("baseline","none",(),0.0,0.0,1.0,0.0,("reference case",)),
        Intervention("demand-flex-5","demand_flexibility",("montreal","monteregie","capitale-nationale"),0.05,1.2,0.95,0.2,("voluntary response available",)),
        Intervention("storage-regional","storage",("montreal","cote-nord","outaouais"),900.0,4.8,0.85,0.55,("synthetic dispatch abstraction",)),
        Intervention("corridor-hardening","hardening",("cote-nord","saguenay-lac-saint-jean","bas-saint-laurent"),0.32,7.5,0.35,0.8,("fixture corridors only",)),
        Intervention("distributed-resilience","distributed_generation",("gaspesie-iles","outaouais","estrie"),420.0,5.9,0.72,0.65,("aggregate non-operational model",)),
        Intervention("combined-adaptive","portfolio",("montreal","monteregie","cote-nord","outaouais"),1.0,8.8,0.55,0.75,("combines demand, storage and modest hardening",)),
    )

def apply_intervention(regions: dict[str,RegionState], corridors: tuple[Corridor,...], scenario: Scenario, intervention: Intervention) -> tuple[dict[str,RegionState],tuple[Corridor,...],Scenario]:
    r=dict(regions); c=list(corridors); s=scenario
    if intervention.kind=="demand_flexibility":
        for rid in intervention.target_regions:
            x=r[rid]; r[rid]=replace(x,demand_mw=x.demand_mw*(1.0-intervention.magnitude))
    elif intervention.kind=="storage":
        per=intervention.magnitude/max(len(intervention.target_regions),1)
        for rid in intervention.target_regions:
            x=r[rid]; r[rid]=replace(x,generation_mw=x.generation_mw+per,storage_mwh=x.storage_mwh+per*3)
    elif intervention.kind=="hardening":
        targets=set(intervention.target_regions)
        c=[replace(x,climate_exposure=x.climate_exposure*(1-intervention.magnitude),repair_hours=x.repair_hours*0.8) if x.source in targets or x.target in targets else x for x in c]
    elif intervention.kind=="distributed_generation":
        per=intervention.magnitude/max(len(intervention.target_regions),1)
        for rid in intervention.target_regions:
            x=r[rid]; r[rid]=replace(x,generation_mw=x.generation_mw+per,reserve_mw=x.reserve_mw+0.25*per)
    elif intervention.kind=="portfolio":
        demand=Intervention("tmp","demand_flexibility",("montreal","monteregie"),0.04,0,1,0)
        storage=Intervention("tmp","storage",("cote-nord","outaouais"),600,0,1,0)
        harden=Intervention("tmp","hardening",("cote-nord","bas-saint-laurent"),0.18,0,1,0)
        r,cc,s=apply_intervention(r,tuple(c),s,demand); r,cc,s=apply_intervention(r,cc,s,storage); return apply_intervention(r,cc,s,harden)
    return r,tuple(c),s
