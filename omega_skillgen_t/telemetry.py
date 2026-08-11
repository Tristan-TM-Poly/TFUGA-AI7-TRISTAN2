from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
from typing import Any

REQUIRED_RESULT_FIELDS=("eval_id","passed")


def normalize_behavioral_results(payload: dict[str, Any]) -> dict[str, Any]:
    skill=str(payload.get("skill","unknown")); version=str(payload.get("version","unknown"))
    rows=[]; errors=[]
    for i,row in enumerate(payload.get("results",[])):
        if not isinstance(row,dict):
            errors.append(f"results[{i}] must be an object"); continue
        missing=[k for k in REQUIRED_RESULT_FIELDS if k not in row]
        if missing:
            errors.append(f"results[{i}] missing {','.join(missing)}"); continue
        item=dict(row)
        item["eval_id"]=str(item["eval_id"]); item["passed"]=bool(item["passed"])
        item["class"]=str(item.get("class","unspecified")); item["must_pass"]=bool(item.get("must_pass",False))
        item["dimensions"]=dict(item.get("dimensions",{}) or {})
        rows.append(item)
    return {"skill":skill,"version":version,"results":rows,"errors":errors}


def behavioral_summary(payload: dict[str, Any]) -> dict[str, Any]:
    normalized=normalize_behavioral_results(payload); rows=normalized["results"]
    total=len(rows); passed=sum(1 for r in rows if r["passed"])
    by_class=defaultdict(lambda:Counter(total=0,passed=0))
    for r in rows:
        by_class[r["class"]]["total"]+=1; by_class[r["class"]]["passed"]+=int(r["passed"])
    must_fail=[r["eval_id"] for r in rows if r["must_pass"] and not r["passed"]]
    dimension_values=defaultdict(list)
    for r in rows:
        for key,value in r["dimensions"].items():
            if isinstance(value,(int,float)) and not isinstance(value,bool): dimension_values[key].append(float(value))
    dimensions={k:{"count":len(v),"mean":sum(v)/len(v)} for k,v in dimension_values.items() if v}
    return {
        "skill":normalized["skill"],"version":normalized["version"],"errors":normalized["errors"],
        "total":total,"passed":passed,"pass_rate":(passed/total if total else None),
        "must_pass_failures":must_fail,"by_class":{k:dict(v) for k,v in sorted(by_class.items())},
        "numeric_dimensions":dimensions,
        "behavioral_eval_pass":bool(total and not normalized["errors"] and not must_fail),
        "note":"behavioral_eval_pass only summarizes supplied results; provenance/authenticity must be established separately.",
    }


def split_memory(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    normalized=normalize_behavioral_results(payload); mplus=[]; mminus=[]
    for row in normalized["results"]:
        record={"skill":normalized["skill"],"version":normalized["version"],"eval_id":row["eval_id"],
                "class":row["class"],"evidence":row.get("evidence",""),"dimensions":row["dimensions"]}
        if row["passed"]:
            record["success_mode"]=row.get("success_mode","passed_eval"); mplus.append(record)
        else:
            record["failure_mode"]=row.get("failure_mode","failed_eval")
            record["cause_hypothesis"]=row.get("cause_hypothesis",""); record["repair"]=row.get("repair","")
            mminus.append(record)
    return {"M_PLUS":mplus,"M_MINUS":mminus}


def write_memory_ledgers(payload: dict[str, Any], out_dir: str | Path) -> dict[str, Any]:
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); split=split_memory(payload)
    for key,rows in split.items():
        with (out/f"{key}.jsonl").open("w",encoding="utf-8") as f:
            for row in rows: f.write(json.dumps(row,ensure_ascii=False)+"\n")
    summary=behavioral_summary(payload)
    (out/"BEHAVIORAL_SUMMARY.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return summary
