from __future__ import annotations
import random
from dataclasses import replace
from .models import Scenario

def generate_worlds(base: Scenario, count: int, *, seed: int=20260803) -> tuple[Scenario,...]:
    if count < 1: raise ValueError("count must be positive")
    rng=random.Random(seed); worlds=[]
    for i in range(count):
        worlds.append(replace(base,
            scenario_id=f"{base.scenario_id}:world-{i:05d}",
            demand_multiplier=max(0.75,base.demand_multiplier*rng.uniform(0.90,1.12)),
            hydro_multiplier=max(0.55,base.hydro_multiplier*rng.uniform(0.86,1.10)),
            wind_multiplier=max(0.25,base.wind_multiplier*rng.uniform(0.70,1.30)),
            ice_severity=min(1.0,max(0.0,base.ice_severity+rng.uniform(-0.12,0.12))),
            wind_severity=min(1.0,max(0.0,base.wind_severity+rng.uniform(-0.15,0.15))),
            logistics_delay=min(1.0,max(0.0,base.logistics_delay+rng.uniform(-0.12,0.18))),
            workforce_availability=min(1.0,max(0.35,base.workforce_availability*rng.uniform(0.82,1.10))),
            seed=seed+i,
            metadata={**base.metadata,"generated_world":True,"world_index":i},
        ))
    return tuple(worlds)
