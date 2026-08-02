from __future__ import annotations
from dataclasses import dataclass
from typing import Callable,Iterable,Sequence
import math,random
from .models import U2Tensor
@dataclass(frozen=True)
class Interval:
    low:float; high:float
    def __post_init__(self):
        if not(math.isfinite(self.low) and math.isfinite(self.high) and self.low<=self.high): raise ValueError('invalid interval')
    @property
    def width(self): return self.high-self.low
    def contains(self,value): return self.low<=value<=self.high
    def intersect(self,other):
        low=max(self.low,other.low); high=min(self.high,other.high); return None if low>high else Interval(low,high)
def combine_independent_standard_uncertainties(values:Iterable[float])->float:
    values=tuple(values)
    if any(v<0 or not math.isfinite(v) for v in values): raise ValueError('uncertainties must be finite and non-negative')
    return math.sqrt(sum(v*v for v in values))
def u2_from_coverage(*,measurement_coverage,provenance_coverage,model_validation,repeatability):
    vals=(measurement_coverage,provenance_coverage,model_validation,repeatability)
    if any(not 0<=v<=1 for v in vals): raise ValueError('coverage values must lie in [0,1]')
    return U2Tensor(1-repeatability,1-model_validation,max(0.0,1-model_validation*0.8),1-measurement_coverage,1-provenance_coverage,max(0.05,1-(measurement_coverage+provenance_coverage+model_validation)/3))
def monte_carlo(function:Callable[...,float],samplers:Sequence[Callable[[random.Random],float]],*,samples=10000,seed=0):
    if samples<=0: raise ValueError('samples must be positive')
    rng=random.Random(seed); values=[float(function(*(sampler(rng) for sampler in samplers))) for _ in range(samples)]; values.sort(); mean=sum(values)/samples; variance=sum((value-mean)**2 for value in values)/(samples-1 if samples>1 else 1)
    def quantile(p): return values[min(samples-1,max(0,int(round(p*(samples-1)))))]
    return {'samples':samples,'seed':seed,'mean':mean,'std':math.sqrt(variance),'q05':quantile(.05),'q50':quantile(.5),'q95':quantile(.95)}
def normal(mean,std):
    if std<0: raise ValueError('std must be non-negative')
    return lambda rng:rng.gauss(mean,std)
def uniform(low,high):
    if high<low: raise ValueError('invalid bounds')
    return lambda rng:rng.uniform(low,high)
