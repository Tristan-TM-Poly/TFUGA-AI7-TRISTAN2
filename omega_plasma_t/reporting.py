import json
from pathlib import Path
def write_report(state,report,output_dir:Path):
    output_dir.mkdir(parents=True,exist_ok=True); payload={"state":state.to_dict(),"oak":report.to_dict()}
    (output_dir/"plasma-report.json").write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    a=report.assessment; m=report.model_decision
    lines=["# Ω-PLASMA-T∞ assessment","",f"**OAK status:** `{report.status}`",f"**Epistemic status:** `{report.epistemic_status}`","","## Regime labels"]+[f"- `{x}`" for x in (a.labels if a else ())]+["","## Recommended models"]+[f"- **{x.name}** — score {x.score:.3f}: {'; '.join(x.reasons) or 'rule-based candidate'}" for x in (m.recommended if m else ())]+["","## OAK findings"]+[f"- **{x.severity.upper()} {x.code}:** {x.message} Remediation: {x.remediation}" for x in report.findings]+["","## Scientific status","Deterministic model-selection aid, not experimental certification or safety authorization."]
    (output_dir/"plasma-report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return {"json":str(output_dir/"plasma-report.json"),"markdown":str(output_dir/"plasma-report.md")}
