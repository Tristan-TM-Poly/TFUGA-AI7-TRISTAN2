import argparse,json
from pathlib import Path
from .core import load_json,validate_spec,generate_skill,lint_skill,eval_coverage,evolve_failures
from .trust import scan_skill_trust
from .meta import compose_specs,generate_domain_generator,mutate_spec,compare_specs
from .mining import mine_workflows,proposals_from_workflows
from .catalog import catalog_skills,build_skill_hypergraph

def emit(x): print(json.dumps(x,ensure_ascii=False,indent=2))

def main():
    p=argparse.ArgumentParser(prog="omega-skillgen"); s=p.add_subparsers(dest="cmd",required=True)
    g=s.add_parser("generate"); g.add_argument("spec"); g.add_argument("out")
    l=s.add_parser("lint"); l.add_argument("skill_dir")
    e=s.add_parser("eval"); e.add_argument("skill_dir")
    t=s.add_parser("trust"); t.add_argument("skill_dir")
    c=s.add_parser("check-spec"); c.add_argument("spec")
    v=s.add_parser("evolve"); v.add_argument("results"); v.add_argument("out")
    m=s.add_parser("mine"); m.add_argument("events"); m.add_argument("--min-occurrences",type=int,default=2)
    mp=s.add_parser("mine-proposals"); mp.add_argument("events"); mp.add_argument("out"); mp.add_argument("--threshold",type=float,default=0.5)
    co=s.add_parser("compose"); co.add_argument("name"); co.add_argument("description"); co.add_argument("specs",nargs="+"); co.add_argument("--out-spec")
    dg=s.add_parser("domain-generator"); dg.add_argument("profile"); dg.add_argument("out")
    mu=s.add_parser("mutate"); mu.add_argument("spec"); mu.add_argument("strategy"); mu.add_argument("out")
    df=s.add_parser("diff"); df.add_argument("before"); df.add_argument("after")
    ca=s.add_parser("catalog"); ca.add_argument("root"); ca.add_argument("--graph",action="store_true")
    a=p.parse_args()

    if a.cmd=="generate":
        path=generate_skill(load_json(a.spec),a.out)
        r={"status":"GENERATED","path":str(path),"lint":lint_skill(path),"eval":eval_coverage(path),"trust":scan_skill_trust(path)}
        emit(r); return 0 if r["lint"]["status"]==r["eval"]["status"]=="PASS" else 2
    if a.cmd=="lint":
        r=lint_skill(a.skill_dir); emit(r); return 0 if r["status"]=="PASS" else 2
    if a.cmd=="eval":
        r=eval_coverage(a.skill_dir); emit(r); return 0 if r["status"]=="PASS" else 3
    if a.cmd=="trust":
        r=scan_skill_trust(a.skill_dir); emit(r); return 0 if r["status"]!="REVIEW" else 4
    if a.cmd=="check-spec":
        er=validate_spec(load_json(a.spec)); emit({"status":"PASS" if not er else "FAIL","errors":er}); return 0 if not er else 5
    if a.cmd=="evolve":
        emit(evolve_failures(load_json(a.results),a.out)); return 0
    if a.cmd=="mine":
        emit(mine_workflows(a.events,a.min_occurrences)); return 0
    if a.cmd=="mine-proposals":
        mined=mine_workflows(a.events); props=proposals_from_workflows(mined,a.threshold); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
        files=[]
        for spec in props:
            f=out/f"{spec['name']}.json"; f.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); files.append(str(f))
        emit({"mined":mined,"proposal_count":len(props),"proposal_files":files}); return 0
    if a.cmd=="compose":
        spec=compose_specs([load_json(x) for x in a.specs],a.name,a.description)
        if a.out_spec: Path(a.out_spec).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        emit(spec); return 0
    if a.cmd=="domain-generator":
        spec=generate_domain_generator(load_json(a.profile)); path=generate_skill(spec,a.out)
        emit({"spec":spec,"path":str(path),"lint":lint_skill(path),"eval":eval_coverage(path)}); return 0
    if a.cmd=="mutate":
        spec=mutate_spec(load_json(a.spec),a.strategy); Path(a.out).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        emit({"status":"WROTE_MUTANT","out":a.out,"strategy":a.strategy}); return 0
    if a.cmd=="diff":
        emit(compare_specs(load_json(a.before),load_json(a.after))); return 0
    if a.cmd=="catalog":
        cat=catalog_skills(a.root); emit(build_skill_hypergraph(cat) if a.graph else cat); return 0
    return 1
