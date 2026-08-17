from typing import Any, Iterable, Mapping
from omega_capability_os_t import CapabilityRuntime, compile_workunit
from omega_capability_os_t.core import stable_digest
from .epistemic import Claim, evaluate_claim

def execute_report(computer:Any,work_unit:Any,*,claims:Iterable[Claim]=(),handlers:Mapping[str,Any]|None=None,resolver:Any|None=None,completed_dependencies:Iterable[str]=(),health:Mapping[str,Any]|None=None,candidate_sha:str|None=None,evidence_sha:str|None=None,compile_report_fn:Any=None)->dict[str,Any]:
    claim_list=list(claims); decisions=[evaluate_claim(c) for c in claim_list]
    comp=compile_report_fn(computer,work_unit,completed_dependencies=completed_dependencies,health=health)
    bridge=compile_workunit(work_unit,completed_dependencies=completed_dependencies)
    execution=CapabilityRuntime(handlers=handlers,resolver=resolver).execute(
        bridge.capabilities,bridge.intent,health=dict(health or {}),initial_values=bridge.initial_values,
        candidate_sha=candidate_sha,evidence_sha=evidence_sha,
    )
    residuals=[{"kind":"claim_hold","claim":c.statement,"reason":d.reason} for c,d in zip(claim_list,decisions) if not d.accepted]
    residuals += [{"kind":"unresolved","token":t} for t in execution.get("unresolved_runtime_outputs",[])]
    memory=list(execution.get("outcomes",[]))
    memory += [{"memory":"M?","kind":"claim_hold","claim":c.statement} for c,d in zip(claim_list,decisions) if not d.accepted]
    if execution.get("execution_status")=="COMPLETE" and not execution.get("fresh"):
        memory.append({"memory":"M?","kind":"freshness_hold"})
    status="PASS" if all(d.accepted for d in decisions) and execution.get("oak",{}).get("status")=="PASS" else "HOLD"
    receipt={
        "schema":"omega-ttm-exec-receipt/v1",
        "work_unit_id":work_unit.work_unit_id,
        "compile_fingerprint":comp["fingerprint"],
        "claims":[c.to_dict() for c in claim_list],
        "claim_decisions":[d.to_dict() for d in decisions],
        "execution":execution,
        "residuals":residuals,
        "memory":memory,
        "go_max_min":comp["go_max_min"],
        "oak":{"status":status,"boundary":"PASS covers declared execution, exact SHA freshness and structural claim/evidence compatibility only."},
    }
    receipt["fingerprint"]=stable_digest(receipt)
    return receipt
