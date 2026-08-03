from __future__ import annotations
import json
from pathlib import Path
from .experiment import CampaignReport
from .models import DecisionPackage

def write_decision_bundle(output_dir: Path, report: CampaignReport, decision: DecisionPackage) -> dict[str,str]:
    output_dir.mkdir(parents=True,exist_ok=True)
    report_path=output_dir/"campaign.json"; decision_path=output_dir/"decision-package.json"; md_path=output_dir/"report.md"
    report_path.write_text(json.dumps(report.to_dict(),indent=2,sort_keys=True),encoding="utf-8")
    decision_path.write_text(json.dumps(decision.to_dict(),indent=2,sort_keys=True),encoding="utf-8")
    lines=["# Ω-HQT synthetic decision report","",f"Status: **{decision.status}**","",f"Mission: {decision.mission}","","## Recommended synthetic interventions"]
    lines.extend(f"- `{x}`" for x in decision.recommended_interventions)
    lines.extend(["","## OAK boundaries","- No real Hydro-Québec topology or operational data.","- No operational recommendation or control authority.","- Results are deterministic research fixtures requiring external validation.","","## Chamber votes"])
    lines.extend(f"- **{v.chamber}**: {'PASS' if v.passed else 'BLOCK'} — {v.rationale}" for v in decision.votes)
    md_path.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return {"campaign":str(report_path),"decision":str(decision_path),"markdown":str(md_path)}
