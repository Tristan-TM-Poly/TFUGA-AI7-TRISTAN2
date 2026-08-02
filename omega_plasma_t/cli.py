"""Command line interface for Ω-PLASMA-T∞."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from .state import PlasmaState
from .oak import audit_state
from .reporting import write_report
from .atlas import search_atlas
from .campaign import CampaignAxis,CampaignGenerator,CampaignPolicy

def _parser():
    p=argparse.ArgumentParser(prog="omega-plasma",description="OAK-safe plasma regime compiler")
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("assess",help="assess a JSON plasma state")
    a.add_argument("state_json",type=Path); a.add_argument("--output-dir",type=Path,default=Path("generated/omega_plasma_t"))
    s=sub.add_parser("atlas",help="search all bundled atlases"); s.add_argument("query")
    c=sub.add_parser("campaign",help="emit a parameter campaign without a permanent architecture cap")
    c.add_argument("spec_json",type=Path); c.add_argument("--output",type=Path,default=Path("generated/omega_plasma_t/campaign.jsonl")); c.add_argument("--work-budget",type=int); c.add_argument("--resume-after",type=int,default=0)
    return p

def main(argv=None)->int:
    args=_parser().parse_args(argv)
    if args.cmd=="assess":
        state=PlasmaState.from_dict(json.loads(args.state_json.read_text(encoding="utf-8")))
        report=audit_state(state); paths=write_report(state,report,args.output_dir)
        print(json.dumps({"status":report.status,"paths":paths,"recommended":[x.name for x in report.model_decision.recommended]},indent=2)); return 0 if report.status!="blocked" else 2
    if args.cmd=="atlas":
        print(json.dumps(search_atlas(args.query),indent=2,ensure_ascii=False)); return 0
    if args.cmd=="campaign":
        spec=json.loads(args.spec_json.read_text(encoding="utf-8"))
        axes=[CampaignAxis(x["name"],tuple(x["values"])) for x in spec["axes"]]
        policy=CampaignPolicy(**spec.get("policy",{})); result=CampaignGenerator(axes,policy).emit_jsonl(args.output,args.resume_after,args.work_budget)
        print(json.dumps(result,indent=2)); return 0
    return 1

if __name__=="__main__": raise SystemExit(main())
