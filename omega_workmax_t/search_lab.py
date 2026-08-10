"""R0.6 deterministic beam + multi-fidelity policy search."""
from __future__ import annotations
import hashlib, json
from typing import Any

def _score(m: dict[str, Any]) -> float:
    utility = float(m.get("utility", 0.0))
    evidence = float(m.get("evidence", 0.0))
    risk = float(m.get("risk", 0.0))
    cost = float(m.get("cost", 0.0))
    return utility + 0.25 * evidence - 0.5 * risk - 0.01 * cost

def _dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    aa=(float(a.get("utility",0)),float(a.get("evidence",0)),-float(a.get("risk",0)),-float(a.get("cost",0)))
    bb=(float(b.get("utility",0)),float(b.get("evidence",0)),-float(b.get("risk",0)),-float(b.get("cost",0)))
    return all(x>=y for x,y in zip(aa,bb)) and any(x>y for x,y in zip(aa,bb))

def run_multifidelity_beam(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = {str(c["candidate_id"]): c for c in payload.get("candidates", [])}
    stages = list(payload.get("stages", []))
    if not candidates:
        raise ValueError("at least one candidate is required")
    if not stages:
        raise ValueError("at least one stage is required")
    survivors = sorted(candidates)
    evaluated_cells = 0
    history=[]
    for stage in stages:
        name=str(stage["name"])
        width=max(1,int(stage.get("beam_width",len(survivors))))
        rows=[]
        for cid in survivors:
            metrics=(candidates[cid].get("evaluations") or {}).get(name)
            if metrics is None:
                continue
            evaluated_cells += 1
            rows.append((cid,_score(metrics),metrics))
        rows.sort(key=lambda x:(-x[1],x[0]))
        survivors=[cid for cid,_,_ in rows[:width]]
        history.append({"stage":name,"beam_width":width,"evaluated":len(rows),"survivors":survivors})
        if not survivors:
            break

    final_name=str(stages[-1]["name"])
    exhaustive=[]
    for cid,c in sorted(candidates.items()):
        metrics=(c.get("evaluations") or {}).get(final_name)
        if metrics is not None:
            exhaustive.append((cid,_score(metrics),metrics))
    if not exhaustive:
        raise ValueError("final-stage evaluations are required for regret/Pareto audit")
    exhaustive.sort(key=lambda x:(-x[1],x[0]))
    best_id,best_score,_=exhaustive[0]

    survivor_final=[x for x in exhaustive if x[0] in survivors]
    beam_best_id,beam_best_score = (survivor_final[0][0],survivor_final[0][1]) if survivor_final else (None,float("-inf"))
    exhaustive_pareto=[
        cid for cid,_,metrics in exhaustive
        if not any(other!=cid and _dominates(om,metrics) for other,_,om in exhaustive)
    ]
    beam_pareto=[cid for cid in survivors if cid in exhaustive_pareto]
    total_possible=sum(len(candidates) for _ in stages)
    result={
        "schema":"omega-workmax-beam-multifidelity/v1",
        "candidate_count":len(candidates),
        "stage_count":len(stages),
        "evaluated_cells":evaluated_cells,
        "full_grid_cells":total_possible,
        "evaluation_reduction":0.0 if total_possible==0 else 1.0-evaluated_cells/total_possible,
        "history":history,
        "survivors":survivors,
        "exhaustive_best":best_id,
        "beam_best":beam_best_id,
        "best_score_ratio":0.0 if best_score==0 or beam_best_id is None else beam_best_score/best_score,
        "score_regret":None if beam_best_id is None else best_score-beam_best_score,
        "exhaustive_pareto":exhaustive_pareto,
        "pareto_recall":0.0 if not exhaustive_pareto else len(beam_pareto)/len(exhaustive_pareto),
        "automatic_promotion_authorized":False,
        "oak_limits":[
            "Beam pruning can discard globally useful or Pareto-diverse candidates.",
            "Stage ordering and beam width can change survivors.",
            "A perfect best-score ratio does not imply high Pareto recall.",
            "Synthetic or declared evaluation metrics are not production measurements."
        ]
    }
    canonical=json.dumps(result,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    result["search_digest"]=hashlib.sha256(canonical.encode()).hexdigest()
    return result
