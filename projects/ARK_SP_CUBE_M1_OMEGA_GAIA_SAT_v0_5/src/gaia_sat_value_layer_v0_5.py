"""
GAIA-SAT Value Layer v0.5

Research/simulation only.
Status: SIMULATED_GROSS_CLIMATE_IMPACT_VALUE / MRV_DEPENDENT / NOT_REVENUE / NOT_INVESTMENT_CERTIFIED.
"""

from dataclasses import dataclass
import math

@dataclass
class ClimateLever:
    lever: str
    name: str
    mtco2e_per_year: float
    mrv: float
    readiness: float
    risk: float
    capex_complexity: float

def gross_value_cad(mtco2e_per_year: float, carbon_price_cad_per_t: float) -> float:
    return mtco2e_per_year * 1_000_000.0 * carbon_price_cad_per_t

def mrv_adjusted_value_cad(mtco2e_per_year: float, carbon_price: float, mrv: float) -> float:
    return gross_value_cad(mtco2e_per_year, carbon_price) * mrv

def oak_adjusted_value_cad(mtco2e_per_year: float, carbon_price: float, mrv: float, readiness: float, risk: float) -> float:
    return gross_value_cad(mtco2e_per_year, carbon_price) * mrv * readiness * (1.0 - risk)

def priority_score(mtco2e_per_year: float, mrv: float, readiness: float, risk: float, capex_complexity: float) -> float:
    return math.log1p(mtco2e_per_year) * mrv * readiness * (1.0 - risk) / (0.25 + capex_complexity)

def methane_gwp100_ar6(source_type: str) -> float:
    return 29.8 if source_type in {"fossil", "oil_gas", "coal_mine"} else 27.0

def methane_co2e_tonnes(ch4_tonnes: float, source_type: str) -> float:
    return ch4_tonnes * methane_gwp100_ar6(source_type)

def methane_event_value_cad(ch4_tonnes: float, source_type: str, carbon_price: float) -> float:
    return methane_co2e_tonnes(ch4_tonnes, source_type) * carbon_price

def oak_status_for_claim(has_measurement: bool, has_external_verification: bool, is_financial_claim: bool=False) -> str:
    if is_financial_claim:
        return "BLOCKED_UNLESS_CONTRACT_AND_MRV"
    if has_external_verification:
        return "CERTIFIED_CANDIDATE"
    if has_measurement:
        return "MEASURED"
    return "SIMULATED_OR_ACTIVE"
