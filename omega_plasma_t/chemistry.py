"""Stoichiometric reaction network with OAK checks and simple integration."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Reaction:
    reaction_id: str
    reactants: dict[str,float]
    products: dict[str,float]
    rate_coefficient: float
    order: float | None = None
    threshold_ev: float | None = None
    category: str = "volume"
    provenance: str = "user_supplied"
    def net(self,species:str)->float: return self.products.get(species,0)-self.reactants.get(species,0)
    def rate(self,c:dict[str,float])->float:
        r=self.rate_coefficient
        for name,nu in self.reactants.items(): r*=max(c.get(name,0.0),0.0)**nu
        return r

@dataclass
class ReactionNetwork:
    reactions:list[Reaction]=field(default_factory=list)
    @property
    def species(self)->tuple[str,...]: return tuple(sorted({x for r in self.reactions for x in (*r.reactants,*r.products)}))
    def derivative(self,c:dict[str,float])->dict[str,float]:
        out={s:0.0 for s in self.species}
        for r in self.reactions:
            v=r.rate(c)
            for s in out: out[s]+=r.net(s)*v
        return out
    def euler(self,c0:dict[str,float],dt_s:float,steps:int,clip:bool=True)->list[dict[str,float]]:
        if dt_s<=0 or steps<0: raise ValueError("dt_s>0 and steps>=0 required")
        c={s:float(c0.get(s,0.0)) for s in self.species}; hist=[dict(c)]
        for _ in range(steps):
            dc=self.derivative(c); c={s:(max(0.0,c[s]+dt_s*dc[s]) if clip else c[s]+dt_s*dc[s]) for s in c}; hist.append(dict(c))
        return hist
    def stoichiometric_matrix(self)->dict[str,dict[str,float]]: return {s:{r.reaction_id:r.net(s) for r in self.reactions} for s in self.species}
    def audit(self)->dict:
        issues=[]; ids=set()
        for r in self.reactions:
            if r.reaction_id in ids: issues.append(f"duplicate reaction id: {r.reaction_id}")
            ids.add(r.reaction_id)
            if r.rate_coefficient<0: issues.append(f"negative rate coefficient: {r.reaction_id}")
            if not r.reactants: issues.append(f"source reaction needs explicit provenance: {r.reaction_id}")
            if not r.products: issues.append(f"sink reaction needs explicit provenance: {r.reaction_id}")
        return {"status":"passed" if not issues else "review","issues":issues,"reaction_count":len(self.reactions),"species_count":len(self.species)}
