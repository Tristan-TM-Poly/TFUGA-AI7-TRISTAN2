from __future__ import annotations
from .models import Scenario

def nominal(seed: int=0) -> Scenario:
    return Scenario("nominal",seed=seed,metadata={"fixture":True})

def winter_peak(seed: int=1) -> Scenario:
    return Scenario("winter-peak",1.24,0.96,0.82,-28.0,0.15,0.2,0.0,0.1,0.95,seed,{"fixture":True})

def compound_ice_storm(seed: int=2) -> Scenario:
    return Scenario("compound-ice-storm",1.31,0.91,0.55,-24.0,0.88,0.62,0.0,0.55,0.68,seed,{"fixture":True,"operational_claim":False})

def climate_stress(seed: int=3) -> Scenario:
    return Scenario("climate-stress",1.08,0.78,0.72,32.0,0.0,0.45,0.62,0.35,0.82,seed,{"fixture":True})

def catalog() -> tuple[Scenario,...]: return (nominal(),winter_peak(),compound_ice_storm(),climate_stress())
