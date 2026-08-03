from __future__ import annotations
from dataclasses import dataclass, asdict
from .experiment import run_campaign
from .hashutil import sha256
from .hypergraph import EnergyHypergraph
from .interventions import catalog
from .outage import simulate_outage
from .parliament import deliberate
from .scenarios import compound_ice_storm, nominal
from .security import safety_gate
from .synthetic_quebec import build_corridors, build_regions, build_synthetic_quebec

@dataclass(frozen=True)
class BenchmarkCheck:
    name: str; passed: bool; detail: str
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class OAKBenchReport:
    status: str
    checks: tuple[BenchmarkCheck,...]
    metrics: dict
    claims: dict
    evidence_hash: str
    @property
    def passed(self): return all(x.passed for x in self.checks)
    def to_dict(self):
        d=asdict(self); d["checks"]=[x.to_dict() for x in self.checks]; d["passed"]=self.passed; return d

def run_oak_benchmarks(world_count: int=32) -> OAKBenchReport:
    graph=build_synthetic_quebec(); regions=build_regions(); corridors=build_corridors()
    nominal_flow=simulate_outage(regions,corridors,nominal())
    storm=simulate_outage(regions,corridors,compound_ice_storm())
    campaign_a=run_campaign(compound_ice_storm(),catalog(),world_count=world_count)
    campaign_b=run_campaign(compound_ice_storm(),catalog(),world_count=world_count)
    decision=deliberate(campaign_a)
    blocked=safety_gate(requested_level="public",content="live switching command and relay setting",public_data_only=True)
    checks=(
        BenchmarkCheck("hypergraph-valid",not graph.validate(),str(graph.validate())),
        BenchmarkCheck("synthetic-node-count",len(graph.nodes)>=38,f"nodes={len(graph.nodes)}"),
        BenchmarkCheck("nominal-flow-finite",nominal_flow.flow.finite,"finite DC abstraction"),
        BenchmarkCheck("energy-balance-residual",nominal_flow.flow.balance_residual_mw<1e-7,f"residual={nominal_flow.flow.balance_residual_mw}"),
        BenchmarkCheck("storm-not-better-than-nominal",storm.flow.unserved_energy_mwh>=nominal_flow.flow.unserved_energy_mwh,"monotonic fixture stress"),
        BenchmarkCheck("campaign-deterministic",campaign_a.evidence_hash==campaign_b.evidence_hash,campaign_a.evidence_hash),
        BenchmarkCheck("world-count",len(campaign_a.outcomes)==world_count*len(catalog()),f"outcomes={len(campaign_a.outcomes)}"),
        BenchmarkCheck("security-refusal",not blocked.allowed,blocked.level),
        BenchmarkCheck("no-real-grid-claim",not campaign_a.claims["real_grid_validated"],"claim boundary preserved"),
        BenchmarkCheck("parliament-pass",decision.status=="SYNTHETIC_DECISION_SUPPORT_PASS",decision.status),
    )
    metrics={"nodes":len(graph.nodes),"hyperedges":len(graph.hyperedges),"corridors":len(corridors),"regions":len(regions),"worlds":world_count,"outcomes":len(campaign_a.outcomes),"nominal_unserved_energy_mwh":nominal_flow.flow.unserved_energy_mwh,"storm_unserved_energy_mwh":storm.flow.unserved_energy_mwh,"pareto_count":len(campaign_a.pareto_interventions)}
    claims={"hydro_quebec_affiliation_claimed":False,"operational_grid_replica_claimed":False,"real_data_validation_claimed":False,"synthetic_research_kernel_claimed":True}
    core={"checks":[x.to_dict() for x in checks],"metrics":metrics,"claims":claims}
    status="CERTIFIED_SYNTHETIC_PUBLIC_RESEARCH_KERNEL_R0_1" if all(x.passed for x in checks) else "FAILED"
    return OAKBenchReport(status,checks,metrics,claims,sha256(core))
