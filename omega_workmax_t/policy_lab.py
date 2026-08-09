"""R0.8 offline scheduler-policy comparison and promotion-plan compiler."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any, Iterable

@dataclass(frozen=True)
class PolicyOutcome:
    policy_id:str
    scenario:str
    completed:bool
    wall_seconds:float
    evidence_coverage:float
    closure_ratio:float
    fanout_factor:float
    regressions:int=0
    risk:float=0.0
    def __post_init__(self):
        if self.wall_seconds<0 or self.fanout_factor<0 or self.regressions<0 or self.risk<0: raise ValueError("negative metric")
        if not 0<=self.evidence_coverage<=1 or not 0<=self.closure_ratio<=1: raise ValueError("coverage/closure must be unit interval")

def _aggregate(rows:list[PolicyOutcome])->dict[str,Any]:
    n=len(rows)
    return {
        "scenario_count":n,
        "completed_all":bool(rows) and all(r.completed for r in rows),
        "mean_wall_seconds":sum(r.wall_seconds for r in rows)/max(1,n),
        "mean_evidence_coverage":sum(r.evidence_coverage for r in rows)/max(1,n),
        "mean_closure_ratio":sum(r.closure_ratio for r in rows)/max(1,n),
        "mean_fanout_factor":sum(r.fanout_factor for r in rows)/max(1,n),
        "total_regressions":sum(r.regressions for r in rows),
        "mean_risk":sum(r.risk for r in rows)/max(1,n),
    }

def compare_policies(
    outcomes: Iterable[PolicyOutcome],
    *,
    incumbent_policy_id:str,
    minimum_wall_improvement:float=0.02,
)->dict[str,Any]:
    by={}
    for row in outcomes: by.setdefault(row.policy_id,[]).append(row)
    if incumbent_policy_id not in by: raise ValueError("incumbent missing")
    aggregates={pid:_aggregate(sorted(rows,key=lambda r:r.scenario)) for pid,rows in sorted(by.items())}
    base=aggregates[incumbent_policy_id]
    eligible=[]
    for pid,a in aggregates.items():
        if pid==incumbent_policy_id: continue
        same_or_better_evidence=a["mean_evidence_coverage"]>=base["mean_evidence_coverage"]
        same_or_better_closure=a["mean_closure_ratio"]>=base["mean_closure_ratio"]
        no_more_regressions=a["total_regressions"]<=base["total_regressions"]
        completed=a["completed_all"]
        improvement=0.0 if base["mean_wall_seconds"]<=0 else (base["mean_wall_seconds"]-a["mean_wall_seconds"])/base["mean_wall_seconds"]
        if completed and same_or_better_evidence and same_or_better_closure and no_more_regressions and improvement>=minimum_wall_improvement:
            eligible.append((pid,improvement,a))
    eligible.sort(key=lambda x:(-x[1],x[2]["mean_fanout_factor"],x[2]["mean_risk"],x[0]))
    selected=eligible[0] if eligible else None
    decision="PROMOTE_CANDIDATE_FOR_HUMAN_REVIEW" if selected else "HOLD_INCUMBENT"
    result={
        "schema":"omega-workmax-policy-lab/v1",
        "incumbent":incumbent_policy_id,
        "aggregates":aggregates,
        "decision":decision,
        "selected_policy":selected[0] if selected else None,
        "improvement_ratio":selected[1] if selected else 0.0,
        "requires_human_approval":True,
        "automatic_source_mutation":False,
        "automatic_merge_authorized":False,
        "oak_limits":[
            "Promotion is based only on supplied scenarios and metrics.",
            "Wall-time improvement cannot compensate for evidence loss, closure regression, or added regressions.",
            "A promotion decision is a review plan, not authority to modify GitHub."
        ]
    }
    canonical=json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    result["report_digest"]=hashlib.sha256(canonical.encode()).hexdigest()
    return result
