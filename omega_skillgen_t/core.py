from __future__ import annotations
from pathlib import Path
import json, re, shutil
from typing import Any

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

class SkillSpecError(ValueError):
    pass

def load_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        obj=json.load(f)
    if not isinstance(obj, dict):
        raise SkillSpecError("top-level JSON must be an object")
    return obj

def validate_spec(spec: dict[str, Any]) -> list[str]:
    errors=[]
    req=("name","description","purpose","use_when","workflow","invariants","outputs","eval_cases")
    for k in req:
        if k not in spec: errors.append(f"missing required field: {k}")
    name=spec.get("name")
    if not isinstance(name,str) or not NAME_RE.fullmatch(name):
        errors.append("name must be lowercase alphanumeric words separated by single hyphens")
    desc=spec.get("description")
    if not isinstance(desc,str) or len(desc.strip())<10:
        errors.append("description must contain at least 10 non-whitespace characters")
    for k in ("use_when","workflow","invariants","outputs","eval_cases"):
        v=spec.get(k)
        if not isinstance(v,list) or not v: errors.append(f"{k} must be a non-empty list")
    valid={"positive","negative","incomplete","edge","adversarial"}
    ids=set()
    for i,c in enumerate(spec.get("eval_cases",[]) if isinstance(spec.get("eval_cases"),list) else []):
        if not isinstance(c,dict):
            errors.append(f"eval_cases[{i}] must be an object"); continue
        for f in ("id","prompt","class"):
            if not c.get(f): errors.append(f"eval_cases[{i}] missing {f}")
        if c.get("class") not in valid: errors.append(f"eval_cases[{i}] has invalid class {c.get('class')!r}")
        cid=c.get("id")
        if cid in ids: errors.append(f"duplicate eval id: {cid}")
        if isinstance(cid,str): ids.add(cid)
    return errors

def _bullets(xs): return "\n".join(f"- {x}" for x in xs) if xs else "- None declared."
def _numbered(xs): return "\n".join(f"{i}. {x}" for i,x in enumerate(xs,1))

def render_skill_md(spec):
    errors=validate_spec(spec)
    if errors: raise SkillSpecError("; ".join(errors))
    return f"""---
name: {spec['name']}
description: {spec['description']}
---

# {spec['name']}

## Purpose

{spec['purpose']}

## Activate for

{_bullets(spec.get('use_when', []))}

## Do not activate for

{_bullets(spec.get('do_not_use_when', []))}

## Workflow

{_numbered(spec.get('workflow', []))}

## OAK invariants

{_bullets(spec.get('invariants', []))}

## Tool/action boundaries

{_bullets(spec.get('tool_policy', []))}

## Outputs

{_bullets(spec.get('outputs', []))}

## Definition of done

{_bullets(spec.get('definition_of_done', []))}

## Evaluation contract

Use `evals/cases.jsonl` for activation boundaries and behavioral test cases.
Static validation is not behavioral proof. External writes, merges, deletions,
sending, payments, publication, and sensitive actions remain subject to the real
tool permissions and approval requirements.
"""

def generate_skill(spec,out_root):
    errors=validate_spec(spec)
    if errors: raise SkillSpecError("; ".join(errors))
    out_root=Path(out_root); d=out_root/spec["name"]
    if d.exists(): shutil.rmtree(d)
    (d/"evals").mkdir(parents=True); (d/"references").mkdir()
    (d/"SKILL.md").write_text(render_skill_md(spec),encoding="utf-8")
    (d/"SkillSpec.json").write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (d/"evals/cases.jsonl").open("w",encoding="utf-8") as f:
        for case in spec["eval_cases"]:
            c=dict(case); c.setdefault("should_trigger",c.get("class")!="negative")
            f.write(json.dumps(c,ensure_ascii=False)+"\n")
    (d/"references/provenance.json").write_text(json.dumps({
        "generator":"omega-skillgen-t","generator_version":"0.2.0",
        "status":"GENERATED_CANDIDATE","behavioral_validation":False
    },indent=2)+"\n",encoding="utf-8")
    return d

def _frontmatter(text):
    if not text.startswith("---\n"): return {},["SKILL.md must begin with YAML front matter"]
    end=text.find("\n---",4)
    if end<0: return {},["SKILL.md front matter is not closed"]
    meta={}; errors=[]
    for line in text[4:end].splitlines():
        if not line.strip(): continue
        if ":" not in line: errors.append(f"invalid front matter line: {line}"); continue
        k,v=line.split(":",1); meta[k.strip()]=v.strip()
    return meta,errors

def lint_skill(skill_dir):
    skill_dir=Path(skill_dir)
    files=[p for p in skill_dir.rglob("*") if p.is_file()]
    manifests=[p for p in files if p.name.lower()=="skill.md"]
    errors=[]; warnings=[]
    if len(manifests)!=1:
        errors.append(f"expected exactly one SKILL.md, found {len(manifests)}")
    else:
        text=manifests[0].read_text(encoding="utf-8",errors="replace")
        meta,e=_frontmatter(text); errors+=e
        if not NAME_RE.fullmatch(meta.get("name","")): errors.append("front matter name is invalid")
        desc=meta.get("description","")
        if not desc: errors.append("front matter description is required")
        elif len(desc)<24: warnings.append("description may be too short to provide strong activation boundaries")
        if "## Workflow" not in text: warnings.append("missing explicit Workflow section")
        if "## OAK invariants" not in text and "## Invariants" not in text: warnings.append("missing explicit invariant section")
    return {"status":"PASS" if not errors else "FAIL","path":str(skill_dir),
            "file_count":len(files),"total_bytes":sum(p.stat().st_size for p in files),
            "errors":errors,"warnings":warnings}

def eval_coverage(skill_dir):
    path=Path(skill_dir)/"evals/cases.jsonl"
    classes={k:0 for k in ("positive","negative","incomplete","edge","adversarial")}
    errors=[]; count=0; ids=set()
    if not path.exists():
        return {"status":"FAIL","count":0,"classes":classes,"errors":["missing evals/cases.jsonl"]}
    for line_no,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        count+=1
        try: c=json.loads(line)
        except json.JSONDecodeError as e: errors.append(f"line {line_no}: {e}"); continue
        cid=c.get("id")
        if cid in ids: errors.append(f"line {line_no}: duplicate id {cid}")
        if isinstance(cid,str): ids.add(cid)
        cls=c.get("class")
        if cls not in classes: errors.append(f"line {line_no}: invalid class {cls!r}"); continue
        classes[cls]+=1
        if c.get("should_trigger") is not None and c["should_trigger"]!=(cls!="negative"):
            errors.append(f"line {line_no}: inconsistent should_trigger")
    if not (classes["positive"] and classes["negative"] and classes["incomplete"] and (classes["edge"]+classes["adversarial"])):
        errors.append("need positive + negative + incomplete + (edge or adversarial) coverage")
    return {"status":"PASS" if not errors else "FAIL","count":count,"classes":classes,"errors":errors}

def evolve_failures(results,out_dir):
    out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    failures=[r for r in results.get("results",[]) if not r.get("passed",False)]
    m=[]
    for r in failures:
        m.append({"skill":results.get("skill","unknown"),"version":results.get("version","unknown"),
                  "eval_id":r.get("eval_id"),"failure_mode":r.get("failure_mode","unspecified"),
                  "evidence":r.get("evidence",""),"cause_hypothesis":r.get("cause_hypothesis",""),
                  "repair":r.get("repair",""),"regression_case":r.get("eval_id")})
    with (out_dir/"M_MINUS.jsonl").open("w",encoding="utf-8") as f:
        for row in m: f.write(json.dumps(row,ensure_ascii=False)+"\n")
    plan={"skill":results.get("skill","unknown"),"source_version":results.get("version","unknown"),
          "promotion_status":"BLOCKED" if failures else "NO_FAILURES",
          "repairs":[{"eval_id":x["eval_id"],"must_become_regression":True,"proposed_change":x["repair"]} for x in m]}
    (out_dir/"repair_plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return plan
