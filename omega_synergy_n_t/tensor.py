"""Sparse symmetric interaction tensor indexed by unordered component sets."""
from __future__ import annotations
from dataclasses import dataclass,field
from .models import canonical_components

@dataclass
class SparseInteractionTensor:
    values: dict[tuple[str,...],float]=field(default_factory=dict)
    metadata: dict[tuple[str,...],dict]=field(default_factory=dict)

    def set(self,components,value,**metadata):
        key=canonical_components(components)
        if not key: raise ValueError("empty interaction belongs to the baseline, not the tensor")
        self.values[key]=float(value); self.metadata[key]=dict(metadata)

    def get(self,components,default=0.0): return self.values.get(canonical_components(components),default)
    def order_slice(self,order): return {k:v for k,v in self.values.items() if len(k)==order}
    def positive(self,threshold=0.0): return {k:v for k,v in self.values.items() if v>threshold}
    def negative(self,threshold=0.0): return {k:v for k,v in self.values.items() if v<-threshold}
    def top(self,n=10,absolute=False):
        if n<0: raise ValueError("n must be non-negative")
        key=(lambda kv:abs(kv[1])) if absolute else (lambda kv:kv[1])
        return sorted(self.values.items(),key=lambda kv:(-key(kv),kv[0]))[:n]
    def sparsity(self,component_count,max_order):
        from math import comb
        possible=sum(comb(component_count,k) for k in range(1,min(component_count,max_order)+1))
        return 1-len(self.values)/(possible or 1)
    def to_dict(self):
        return {"entries":[{"components":list(k),"order":len(k),"value":v,"metadata":self.metadata.get(k,{})} for k,v in sorted(self.values.items(),key=lambda kv:(len(kv[0]),kv[0]))]}
