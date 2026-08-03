from __future__ import annotations
import random
from dataclasses import dataclass, asdict
from .hashutil import sha256
from .models import Corridor, FlowResult, Scenario, RegionState
from .powerflow import run_dc_power_flow

@dataclass(frozen=True)
class OutageSimulation:
    failed_corridors: tuple[str,...]
    cascaded_corridors: tuple[str,...]
    restoration_hours: float
    flow: FlowResult
    evidence_hash: str
    def to_dict(self):
        d=asdict(self); d["flow"]=self.flow.to_dict(); return d

def failure_probability(c: Corridor, s: Scenario) -> float:
    hazard=0.44*s.ice_severity+0.28*s.wind_severity+0.18*s.wildfire_severity+0.10*s.logistics_delay
    return min(0.92,max(0.0,0.005+c.climate_exposure*hazard*0.38))

def simulate_outage(regions: dict[str,RegionState], corridors: tuple[Corridor,...], scenario: Scenario, *, max_cascade_rounds: int=3) -> OutageSimulation:
    rng=random.Random(scenario.seed)
    failed={c.corridor_id for c in corridors if rng.random()<failure_probability(c,scenario)}
    initial=set(failed); last_flow=None
    for _ in range(max_cascade_rounds):
        last_flow=run_dc_power_flow(regions,corridors,unavailable=failed,demand_multiplier=scenario.demand_multiplier,generation_multiplier=scenario.hydro_multiplier,outage_duration_h=1.0)
        new=set()
        for cid,excess in last_flow.overloads_mw.items():
            c=next(x for x in corridors if x.corridor_id==cid)
            p=min(0.8,0.1+excess/max(c.capacity_mw,1.0))
            if rng.random()<p:new.add(cid)
        new-=failed
        if not new: break
        failed|=new
    assert last_flow is not None
    failed_objs=[c for c in corridors if c.corridor_id in failed]
    if failed_objs:
        base=max(c.repair_hours for c in failed_objs)
        restoration=base*(1.0+scenario.logistics_delay)/max(scenario.workforce_availability,0.2)
    else: restoration=0.0
    cascaded=failed-initial
    payload={"initial":sorted(initial),"cascaded":sorted(cascaded),"restoration":restoration,"flow":last_flow.to_dict(),"scenario":scenario.to_dict()}
    return OutageSimulation(tuple(sorted(initial)),tuple(sorted(cascaded)),restoration,last_flow,sha256(payload))
