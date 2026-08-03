from __future__ import annotations
import argparse,json
from pathlib import Path
from typing import Sequence
from .causal import build_outage_hypotheses
from .cvcd import compress_outcomes
from .experiment import run_campaign
from .interventions import catalog
from .gridbench import benchmark_manifest
from .mission import compile_mission
from .oak import run_oak_benchmarks
from .organization import build_public_capability_mirror
from .parliament import deliberate
from .report import write_decision_bundle
from .scenarios import compound_ice_storm
from .synthetic_quebec import build_synthetic_quebec

def parser():
    p=argparse.ArgumentParser(prog="omega-hqt",description="Ω-HYDROQUÉBEC-TRISTAN-T∞ public/synthetic hypergraph mirror research kernel")
    sub=p.add_subparsers(dest="command",required=True)
    b=sub.add_parser("benchmark"); b.add_argument("--worlds",type=int,default=32); b.add_argument("--output")
    m=sub.add_parser("mirror"); m.add_argument("--organization",action="store_true"); m.add_argument("--output")
    c=sub.add_parser("campaign"); c.add_argument("--worlds",type=int,default=64); c.add_argument("--output-dir",default="generated/omega_hqt_t")
    sub.add_parser("cause")
    sub.add_parser("gridbench")
    mission=sub.add_parser("mission"); mission.add_argument("objective")
    return p

def _emit(payload,output=None):
    text=json.dumps(payload,indent=2,sort_keys=True)
    if output: Path(output).write_text(text+"\n",encoding="utf-8")
    print(text)

def main(argv: Sequence[str]|None=None)->int:
    args=parser().parse_args(argv)
    if args.command=="benchmark":
        report=run_oak_benchmarks(args.worlds); _emit(report.to_dict(),args.output); return 0 if report.passed else 2
    if args.command=="mirror":
        graph=build_public_capability_mirror() if args.organization else build_synthetic_quebec(); _emit(graph.to_dict(),args.output); return 0
    if args.command=="gridbench":
        _emit(benchmark_manifest()); return 0
    if args.command=="mission":
        payload=compile_mission(args.objective).to_dict(); _emit(payload); return 0 if payload["status"].startswith("READY") else 2
    if args.command=="cause":
        _emit({"scenario":compound_ice_storm().to_dict(),"hypotheses":[x.to_dict() for x in build_outage_hypotheses(compound_ice_storm())]}); return 0
    report=run_campaign(compound_ice_storm(),catalog(),world_count=args.worlds); decision=deliberate(report); paths=write_decision_bundle(Path(args.output_dir),report,decision)
    summary={"status":decision.status,"worlds":args.worlds,"outcomes":len(report.outcomes),"pareto":report.pareto_interventions,"recommended":decision.recommended_interventions,"paths":paths,"evidence_hash":decision.evidence_hash}
    _emit(summary); return 0 if decision.status.endswith("PASS") else 2

if __name__=="__main__": raise SystemExit(main())
