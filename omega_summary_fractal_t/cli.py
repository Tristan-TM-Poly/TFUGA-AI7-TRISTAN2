from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from .render import render_markdown,write_bundle,write_operational_views
from .summarizer import AUDIENCES,SummaryEngine

def _parser():
 p=argparse.ArgumentParser(prog="omega-summary",description="Ω-SUMMARY-FRACTAL-T∞ deterministic multi-depth repository summarizer");s=p.add_subparsers(dest="command",required=True)
 g=s.add_parser("generate");g.add_argument("root",nargs="?",default=".");g.add_argument("--depth",type=int,default=3);g.add_argument("--audience",choices=sorted(AUDIENCES),default="tristan");g.add_argument("--focus");g.add_argument("--output-dir");g.add_argument("--json",action="store_true",dest="json_stdout");g.add_argument("--max-files",type=int,default=20000)
 a=s.add_parser("all-depths");a.add_argument("root",nargs="?",default=".");a.add_argument("--audience",choices=sorted(AUDIENCES),default="tristan");a.add_argument("--focus");a.add_argument("--output-dir",default=".omega/summary");a.add_argument("--max-files",type=int,default=20000)
 u=s.add_parser("audit");u.add_argument("root",nargs="?",default=".");u.add_argument("--max-files",type=int,default=20000);u.add_argument("--fail-on-gap",action="store_true");return p

def cmd_generate(args):
 b=SummaryEngine(args.root,max_files=args.max_files).generate(depth=args.depth,audience=args.audience,focus=args.focus)
 if args.output_dir:
  paths=write_bundle(b,args.output_dir)
  if args.depth>=3:paths.update(write_operational_views(b,args.output_dir))
  print(json.dumps({k:str(v) for k,v in paths.items()},sort_keys=True))
 elif args.json_stdout:print(json.dumps(b.to_dict(),indent=2,sort_keys=True,ensure_ascii=False))
 else:print(render_markdown(b))
 return 0

def cmd_all_depths(args):
 e=SummaryEngine(args.root,max_files=args.max_files);out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True);index=[]
 for d in range(10):
  b=e.generate(depth=d,audience=args.audience,focus=args.focus);paths=write_bundle(b,out);index.append({"depth":d,"fingerprint":b.cache_fingerprint,"markdown":str(paths["markdown"]),"json":str(paths["json"])});write_operational_views(b,out) if d==9 else None
 (out/"depth_index.json").write_text(json.dumps(index,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps({"generated_depths":10,"output_dir":str(out)},sort_keys=True));return 0

def cmd_audit(args):
 b=SummaryEngine(args.root,max_files=args.max_files).generate(depth=8,audience="oak");payload={"valid":not bool(b.gaps),"gap_count":len(b.gaps),"health":b.health,"duplicate_candidates":b.duplicate_candidates,"fingerprint":b.cache_fingerprint};print(json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False));return 2 if args.fail_on_gap and b.gaps else 0

def main(argv=None):
 args=_parser().parse_args(argv)
 return cmd_generate(args) if args.command=="generate" else cmd_all_depths(args) if args.command=="all-depths" else cmd_audit(args) if args.command=="audit" else 1
if __name__=="__main__":sys.exit(main())
