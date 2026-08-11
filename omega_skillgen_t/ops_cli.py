from __future__ import annotations

import argparse
import json

from .core import load_json
from .genome import skill_genome, dedup_report
from .telemetry import behavioral_summary, write_memory_ledgers


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser=argparse.ArgumentParser(prog="omega-skillgen-ops")
    sub=parser.add_subparsers(dest="cmd",required=True)
    genome=sub.add_parser("genome"); genome.add_argument("spec")
    dedup=sub.add_parser("dedup"); dedup.add_argument("specs",nargs="+"); dedup.add_argument("--threshold",type=float,default=0.82)
    telemetry=sub.add_parser("telemetry"); telemetry.add_argument("results")
    memory=sub.add_parser("memory"); memory.add_argument("results"); memory.add_argument("out")
    args=parser.parse_args()
    if args.cmd=="genome": emit(skill_genome(load_json(args.spec))); return 0
    if args.cmd=="dedup": emit(dedup_report([load_json(x) for x in args.specs],args.threshold)); return 0
    if args.cmd=="telemetry": emit(behavioral_summary(load_json(args.results))); return 0
    if args.cmd=="memory": emit(write_memory_ledgers(load_json(args.results),args.out)); return 0
    return 1


if __name__=="__main__":
    raise SystemExit(main())
