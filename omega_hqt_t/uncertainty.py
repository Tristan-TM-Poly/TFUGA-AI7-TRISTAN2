from __future__ import annotations
from dataclasses import asdict, dataclass
import math

@dataclass(frozen=True)
class Interval:
    low: float
    high: float
    confidence: float
    provenance: tuple[str,...]=()
    def __post_init__(self):
        if self.low>self.high: raise ValueError('low cannot exceed high')
        if not 0<self.confidence<=1: raise ValueError('confidence must be in (0,1]')
    def to_dict(self): return asdict(self)
    def __add__(self, other: 'Interval') -> 'Interval':
        return Interval(self.low+other.low,self.high+other.high,min(self.confidence,other.confidence),self.provenance+other.provenance)
    def scale(self, factor: float) -> 'Interval':
        values=(self.low*factor,self.high*factor)
        return Interval(min(values),max(values),self.confidence,self.provenance)

def ratio(numerator: Interval, denominator: Interval) -> Interval:
    if denominator.low<=0<=denominator.high: raise ZeroDivisionError('denominator interval crosses zero')
    values=[a/b for a in (numerator.low,numerator.high) for b in (denominator.low,denominator.high)]
    return Interval(min(values),max(values),min(numerator.confidence,denominator.confidence),numerator.provenance+denominator.provenance)

def combine_independent_sigma(sigmas: list[float]) -> float:
    if any(x<0 for x in sigmas): raise ValueError('sigma must be non-negative')
    return math.sqrt(sum(x*x for x in sigmas))

def uncertainty_budget(items: dict[str,float]) -> dict:
    combined=combine_independent_sigma(list(items.values()))
    total=sum(items.values())
    shares={k:(v/total if total else 0.0) for k,v in sorted(items.items())}
    return {'components':dict(sorted(items.items())),'rss_combined':combined,'linear_upper_bound':total,'shares':shares}
