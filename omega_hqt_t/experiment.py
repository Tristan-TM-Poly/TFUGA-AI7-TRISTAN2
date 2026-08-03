from __future__ import annotations
from dataclasses import dataclass, asdict
from statistics import mean
from .hashutil import sha256
from .interventions import apply_intervention
from .models import Intervention, Scenario, WorldOutcome
from .outage import simulate_outage
from .synthetic_quebec import build_corridors, build_regions
from .world_factory import generate_worlds

@dataclass(frozen=True)
class CampaignReport:
    campaign_id: str
    world_count: int
    intervention_ids: tuple[str,...]
    outcomes: tuple[WorldOutcome,...]
    summaries: dict[str,dict[str,float]]
    pareto_interventions: tuple[str,...]
    claims: dict[str,bool]
    evidence_hash: str
    def to_dict(self):
        d=asdict(self); d["outcomes"]=[o.to_dict() for o in self.outcomes]; return d

def _outcome(world: Scenario, intervention: Intervention) -> WorldOutcome:
    regions,corridors,_=apply_intervention(build_regions(),build_corridors(),world,intervention)
    sim=simulate_outage(regions,corridors,world)
    overload=sum(sim.flow.overloads_mw.values())
    demand=sum(x.demand_mw*world.demand_multiplier for x in regions.values())
    served_fraction=sim.flow.served_load_mw/max(demand,1.0)
    resilience=max(0.0,100.0*(0.55*served_fraction+0.25/(1+sim.restoration_hours/24)+0.20/(1+overload/1000)))
    payload={"world":world.to_dict(),"intervention":intervention.to_dict(),"simulation":sim.to_dict(),"resilience":resilience}
    return WorldOutcome(world.scenario_id,intervention.intervention_id,sim.flow.served_load_mw,sim.flow.unserved_energy_mwh,overload,sim.restoration_hours,intervention.cost_index,resilience,True,sha256(payload))

def _pareto(summaries: dict[str,dict[str,float]]) -> tuple[str,...]:
    ids=sorted(summaries); front=[]
    for candidate in ids:
        c=summaries[candidate]; dominated=False
        for other in ids:
            if other==candidate: continue
            o=summaries[other]
            no_worse=(o["mean_unserved_energy_mwh"]<=c["mean_unserved_energy_mwh"] and o["mean_restoration_hours"]<=c["mean_restoration_hours"] and o["cost_index"]<=c["cost_index"])
            strictly=(o["mean_unserved_energy_mwh"]<c["mean_unserved_energy_mwh"] or o["mean_restoration_hours"]<c["mean_restoration_hours"] or o["cost_index"]<c["cost_index"])
            if no_worse and strictly: dominated=True; break
        if not dominated: front.append(candidate)
    return tuple(front)

def run_campaign(base: Scenario, interventions: tuple[Intervention,...], *, world_count: int=64, seed: int=20260803) -> CampaignReport:
    worlds=generate_worlds(base,world_count,seed=seed); outcomes=tuple(_outcome(w,i) for i in interventions for w in worlds)
    summaries={}
    for intervention in interventions:
        group=[o for o in outcomes if o.intervention_id==intervention.intervention_id]
        summaries[intervention.intervention_id]={
            "mean_unserved_energy_mwh":mean(o.unserved_energy_mwh for o in group),
            "mean_restoration_hours":mean(o.restoration_hours for o in group),
            "mean_resilience_score":mean(o.resilience_score for o in group),
            "worst_unserved_energy_mwh":max(o.unserved_energy_mwh for o in group),
            "cost_index":intervention.cost_index,
        }
    core={"campaign_id":f"campaign:{base.scenario_id}:{world_count}:{seed}","world_count":world_count,"summaries":summaries,"pareto":_pareto(summaries)}
    return CampaignReport(core["campaign_id"],world_count,tuple(i.intervention_id for i in interventions),outcomes,summaries,core["pareto"],{"real_grid_validated":False,"operational_recommendation_claimed":False,"synthetic_comparison_claimed":True},sha256(core))
