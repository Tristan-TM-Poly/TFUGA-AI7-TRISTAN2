"""CLI for Ω-SYNERGY-N-T∞ R2."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from .adapters import signatures_from_creation_dna
from .experiment import compile_design
from .fixtures import pure_triplet,reducible_triplet,anti_order4,synergy_os_order4
from .mobius import decompose_measurements
from .models import SubsetMeasurement
from .oak import hard_gate
from .reporting import audit_bundle,write_bundle
from .search import beam_search
from .spectrum import order_spectrum

FIXTURES={"pure_triplet":pure_triplet,"reducible_triplet":reducible_triplet,"anti_order4":anti_order4,"synergy_os_order4":synergy_os_order4}

def _load_records(path):
    payload=json.loads(Path(path).read_text()); records=payload.get("measurements",payload) if isinstance(payload,dict) else payload
    return [SubsetMeasurement(tuple(x.get("components",[])),float(x["value"]),float(x.get("standard_error",0)),float(x.get("integration_cost",0)),float(x.get("debt",0)),float(x.get("residual_risk",0)),x.get("context_id","default"),tuple(x.get("provenance",[]))) for x in records]

def parser():
    p=argparse.ArgumentParser(description="Exact and bounded n-order synergy laboratory")
    sub=p.add_subparsers(dest="command",required=True)
    d=sub.add_parser("demo"); d.add_argument("--fixture",choices=sorted(FIXTURES),default="synergy_os_order4"); d.add_argument("--output-dir",default="reports/omega-synergy-n-r2")
    dec=sub.add_parser("decompose"); dec.add_argument("--input",required=True); dec.add_argument("--output")
    sp=sub.add_parser("spectrum"); sp.add_argument("--input",required=True); sp.add_argument("--output")
    ex=sub.add_parser("experiment"); ex.add_argument("components",nargs="+"); ex.add_argument("--design",choices=["auto","full","fractional"],default="auto"); ex.add_argument("--replicates",type=int,default=1)
    se=sub.add_parser("search"); se.add_argument("--creation-dna",required=True); se.add_argument("--max-order",type=int,default=6); se.add_argument("--beam-width",type=int,default=64); se.add_argument("--exploration-rate",type=float,default=.15)
    oak=sub.add_parser("oak"); oak.add_argument("--candidate",required=True)
    au=sub.add_parser("audit"); au.add_argument("--bundle-dir",required=True)
    return p

def _emit(payload,path=None):
    text=json.dumps(payload,indent=2,ensure_ascii=False,sort_keys=True)+"\n"
    if path: Path(path).write_text(text,encoding="utf-8")
    else: print(text,end="")

def main(argv=None):
    args=parser().parse_args(argv)
    if args.command=="demo":
        records=FIXTURES[args.fixture](); estimates=decompose_measurements(records); spectrum=order_spectrum(estimates)
        design=compile_design(tuple(sorted({x for r in records for x in r.components})))
        manifest=write_bundle(args.output_dir,{"measurements.json":[r.to_dict() for r in records],"interactions.json":[x.to_dict() for x in estimates],"spectrum.json":spectrum.to_dict(),"experiment.json":design.to_dict()},metadata={"fixture":args.fixture})
        _emit({"output_dir":args.output_dir,"manifest":manifest,"audit":audit_bundle(args.output_dir)}); return 0
    if args.command in ("decompose","spectrum"):
        estimates=decompose_measurements(_load_records(args.input))
        payload=[x.to_dict() for x in estimates] if args.command=="decompose" else order_spectrum(estimates).to_dict()
        _emit(payload,args.output); return 0
    if args.command=="experiment": _emit(compile_design(tuple(args.components),design_type=args.design,replicates=args.replicates).to_dict()); return 0
    if args.command=="search":
        records=json.loads(Path(args.creation_dna).read_text()); sig=signatures_from_creation_dna(records)
        result=beam_search(tuple(sig),sig,max_order=args.max_order,beam_width=args.beam_width,exploration_rate=args.exploration_rate)
        _emit({str(k):[x.to_dict() for x in v] for k,v in result.items()}); return 0
    if args.command=="oak": _emit(hard_gate(json.loads(Path(args.candidate).read_text())).to_dict()); return 0
    if args.command=="audit": _emit(audit_bundle(args.bundle_dir)); return 0
    return 2
