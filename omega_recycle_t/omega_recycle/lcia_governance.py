from __future__ import annotations
from dataclasses import dataclass
from .unit_ontology import unit_def

@dataclass(frozen=True, slots=True)
class MethodDescriptor:
    name:str
    version:str
    publisher:str
    source_url:str
    factor_sha256:str
    license:str|None=None
    def __post_init__(self):
        if not all((self.name,self.version,self.publisher,self.source_url)): raise ValueError("method identity fields required")
        if len(self.factor_sha256)!=64 or any(c not in "0123456789abcdef" for c in self.factor_sha256.lower()):
            raise ValueError("factor_sha256 must be a 64-character hex digest")
        if not self.source_url.startswith("https://"): raise ValueError("source_url must use https")

@dataclass(frozen=True, slots=True)
class GovernedFactor:
    flow_name:str
    input_unit:str
    impact_category:str
    factor:float
    output_unit:str

@dataclass(frozen=True, slots=True)
class GovernedMethod:
    descriptor:MethodDescriptor
    factors:tuple[GovernedFactor,...]
    claim_boundary:str="external_method_identity_and_unit_contract_only_not_lca_certification"

def validate_governed_method(method:GovernedMethod)->None:
    seen=set()
    for f in method.factors:
        unit_def(f.input_unit)
        key=(f.flow_name,f.input_unit,f.impact_category)
        if key in seen: raise ValueError(f"duplicate governed factor: {key}")
        seen.add(key)
