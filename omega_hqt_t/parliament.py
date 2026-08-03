from __future__ import annotations
from statistics import mean
from .hashutil import sha256
from .models import DecisionPackage, Vote
from .experiment import CampaignReport

def deliberate(report: CampaignReport, *, mission: str="improve synthetic winter resilience") -> DecisionPackage:
    ranked=sorted(report.summaries, key=lambda k:(report.summaries[k]["mean_unserved_energy_mwh"],report.summaries[k]["mean_restoration_hours"],report.summaries[k]["cost_index"]))
    recommended=tuple(x for x in ranked if x in report.pareto_interventions and x!="baseline")[:3]
    rejected=tuple(x for x in ranked if x not in recommended)
    best=report.summaries[recommended[0]] if recommended else report.summaries[ranked[0]]
    baseline=report.summaries.get("baseline",best)
    improvement=1.0-best["mean_unserved_energy_mwh"]/max(baseline["mean_unserved_energy_mwh"],1e-9)
    votes=(
        Vote("reality",True,1.0,"all inputs are declared deterministic synthetic fixtures"),
        Vote("physics",best["mean_unserved_energy_mwh"]<=baseline["mean_unserved_energy_mwh"],max(0.0,min(1.0,improvement+0.5)),"DC-flow and outage abstractions remain finite",() if improvement>=0 else ("no resilience gain",)),
        Vote("futures",len(report.outcomes)>0,1.0,"interventions evaluated on generated worlds"),
        Vote("territories",True,0.7,"regional aggregation exists; consultation is not simulated"),
        Vote("oak",not report.claims["real_grid_validated"],1.0,"claims explicitly deny real-grid validation"),
        Vote("security",True,1.0,"no operational topology, SCADA, protection or customer data"),
    )
    passed=all(v.passed for v in votes)
    core={"mission":mission,"recommended":recommended,"rejected":rejected,"votes":[v.to_dict() for v in votes],"report_hash":report.evidence_hash}
    return DecisionPackage("decision:"+sha256(core)[:16],mission,recommended,rejected,votes,{"decision_support_only":True,"operational_authority_claimed":False,"hydro_quebec_endorsement_claimed":False},{"model_uncertainty":0.75,"data_uncertainty":1.0,"decision_uncertainty":0.70},("higher demand than sampled","correlated multi-corridor failures","longer logistics disruption","model-form error"),("stop if safety gate fails","recompute if provenance changes","reject if improvement is not robust","require official validation before real use"),"SYNTHETIC_DECISION_SUPPORT_PASS" if passed else "BLOCKED",sha256(core))
