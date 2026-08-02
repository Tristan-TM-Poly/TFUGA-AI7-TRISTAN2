from __future__ import annotations
from dataclasses import dataclass
from typing import Callable,Iterable
import math
from .models import CandidateCell
from .oak import evaluate_candidate
@dataclass(frozen=True)
class Objective:
    name:str; target:float; tolerance:float; weight:float=1.0; mode:str='target'
    def __post_init__(self):
        if self.tolerance<=0 or self.weight<=0: raise ValueError('positive tolerance and weight required')
        if self.mode not in {'target','maximize','minimize'}: raise ValueError('invalid mode')
@dataclass(frozen=True)
class RankedCandidate:
    candidate:CandidateCell; objective_score:float; oak_score:float; total_score:float; reasons:tuple[str,...]
class SolidCompiler:
    def __init__(self,objectives:Iterable[Objective],constraints:Iterable[Callable[[CandidateCell],tuple[bool,str]]]=()):
        self.objectives=tuple(objectives); self.constraints=tuple(constraints)
        if not self.objectives: raise ValueError('at least one objective required')
    def _score_one(self,c):
        reasons=[]; hard_ok=True
        for constraint in self.constraints:
            ok,reason=constraint(c); hard_ok &= ok
            if not ok: reasons.append(reason)
        scores=[]; weights=[]
        for obj in self.objectives:
            raw=float(c.descriptor.get(obj.name,0.0))
            if obj.mode=='target': score=math.exp(-abs(raw-obj.target)/obj.tolerance)
            elif obj.mode=='maximize': score=1/(1+math.exp(-(raw-obj.target)/obj.tolerance))
            else: score=1/(1+math.exp((raw-obj.target)/obj.tolerance))
            scores.append(score*obj.weight); weights.append(obj.weight)
        objective=sum(scores)/sum(weights); oak=evaluate_candidate(c).aggregate_score
        return RankedCandidate(c,objective,oak,objective*oak if hard_ok else 0.0,tuple(reasons))
    def rank(self,candidates,limit=None):
        ranked=sorted((self._score_one(c) for c in candidates),key=lambda r:(-r.total_score,r.candidate.candidate_id)); return ranked if limit is None else ranked[:limit]
def maximum_defect_criticality(limit:float):
    if not 0<=limit<=1: raise ValueError('limit in [0,1]')
    return lambda c:(float(c.descriptor.get('defect_criticality',1))<=limit,f'defect criticality exceeds {limit}')
