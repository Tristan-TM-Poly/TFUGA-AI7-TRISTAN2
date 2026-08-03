from __future__ import annotations
from dataclasses import asdict, dataclass
from .hashutil import sha256

@dataclass(frozen=True)
class EconomicCase:
    intervention_id: str
    capex_index: float
    opex_index: float
    expected_avoided_unserved_mwh: float
    value_per_unserved_mwh: float
    years: int
    discount_rate: float
    npv_index: float
    benefit_cost_ratio: float
    evidence_hash: str
    def to_dict(self): return asdict(self)

def present_value_annuity(value: float, years: int, discount_rate: float) -> float:
    if years<1: raise ValueError('years must be positive')
    if discount_rate<=-1: raise ValueError('discount rate must exceed -1')
    return sum(value/((1+discount_rate)**year) for year in range(1,years+1))

def evaluate_case(intervention_id: str, *, capex_index: float, opex_index: float, expected_avoided_unserved_mwh: float, value_per_unserved_mwh: float=1.0, years: int=20, discount_rate: float=0.05) -> EconomicCase:
    annual_benefit=max(0.0,expected_avoided_unserved_mwh)*value_per_unserved_mwh
    pv_benefit=present_value_annuity(annual_benefit,years,discount_rate)
    pv_opex=present_value_annuity(opex_index,years,discount_rate)
    total_cost=capex_index+pv_opex
    npv=pv_benefit-total_cost
    ratio=pv_benefit/max(total_cost,1e-12)
    core={'intervention_id':intervention_id,'capex_index':capex_index,'opex_index':opex_index,'expected_avoided_unserved_mwh':expected_avoided_unserved_mwh,'value_per_unserved_mwh':value_per_unserved_mwh,'years':years,'discount_rate':discount_rate,'npv_index':npv,'benefit_cost_ratio':ratio}
    return EconomicCase(**core,evidence_hash=sha256(core))
