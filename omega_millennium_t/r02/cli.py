"""CLI for Ω-MILLENNIUM-T∞ R0.2."""
import argparse,json
from pathlib import Path
from .core import atlas,benchmark,campaign,poincare_benchmark,problem_specs
def main(argv=None):
    p=argparse.ArgumentParser(prog="omega-millennium-r02"); s=p.add_subparsers(dest="cmd",required=True)
    for n in ("atlas","benchmark","specs","poincare-bench"):
        q=s.add_parser(n); q.add_argument("--output")
    q=s.add_parser("campaign"); q.add_argument("--budget",type=int,default=1024); q.add_argument("--output")
    a=p.parse_args(argv)
    result={"atlas":atlas,"benchmark":benchmark,"specs":problem_specs,"poincare-bench":poincare_benchmark}.get(a.cmd,lambda:campaign(a.budget))()
    text=json.dumps(result,sort_keys=True,indent=2)+"\n"
    if a.output: Path(a.output).write_text(text)
    else: print(text,end="")
    return 0
if __name__=="__main__": raise SystemExit(main())
