from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .adapters import github_pr_event_to_document, github_snapshot_to_document, markdown_to_document, summary_bundle_to_document
from .audit import audit_document
from .bibliography import attach_bibliography, bibliography_report, parse_bibtex
from .compiler import DocumentCompiler
from .delta import semantic_delta
from .evidence import evidence_matrix
from .figure_ir import render_figure_ir
from .incremental import rebuild_plan
from .math_ir import render_math
from .metadocument import metadocument_graph
from .models import DocumentIR
from .notation import notation_registry, notation_rename_plan
from .projection import project_depth, project_depths
from .theorem_bundle import write_theorem_bundle
from .uncertainty import uncertainty_ledger
from .universe import build_universe, universe_plan
from .verifier_receipts import verifier_receipt_report


def _load(path: str) -> DocumentIR:
    return DocumentIR.from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))

def _write_json(payload, path=None):
    text=json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if path:
        Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(text,encoding="utf-8")
    else: print(text,end="")

def _write_docir(doc,path): _write_json(doc.to_mapping(),path)

def _compile_pdf(out,engine):
    executable=shutil.which(engine)
    if executable is None:
        print(json.dumps({"pdf":"skipped","reason":f"{engine} not found"})); return 2
    run=subprocess.run([executable,"-interaction=nonstopmode","-halt-on-error","document.tex"],cwd=out,capture_output=True,text=True,timeout=120,check=False)
    (out/"latex-build.stdout.log").write_text(run.stdout,encoding="utf-8"); (out/"latex-build.stderr.log").write_text(run.stderr,encoding="utf-8")
    print(json.dumps({"pdf":"passed" if run.returncode==0 else "failed","returncode":run.returncode})); return run.returncode

def _depths(value):
    items=[int(part.strip()) for part in value.split(",") if part.strip()]
    if not items or any(x<0 for x in items): raise argparse.ArgumentTypeError("depths must be non-empty and >= 0")
    return items

def build_parser():
    p=argparse.ArgumentParser(prog="omega-doc",description="Ω-LATEX-T∞ deterministic evidence-bound document compiler"); sub=p.add_subparsers(dest="command",required=True)
    b=sub.add_parser("build"); b.add_argument("input"); b.add_argument("--output-dir",default="generated/omega_latex_t"); b.add_argument("--allow-audit-errors",action="store_true"); b.add_argument("--pdf",action="store_true"); b.add_argument("--engine",default="pdflatex",choices=["pdflatex","xelatex","lualatex"]); b.add_argument("--depth",type=int)
    inc=sub.add_parser("incremental-build"); inc.add_argument("input"); inc.add_argument("--output-dir",default="generated/omega_latex_t/incremental"); inc.add_argument("--cache-dir",default=".omega-latex-cache"); inc.add_argument("--before"); inc.add_argument("--allow-audit-errors",action="store_true")
    a=sub.add_parser("audit"); a.add_argument("input"); r=sub.add_parser("render"); r.add_argument("input")
    md=sub.add_parser("from-markdown"); md.add_argument("input"); md.add_argument("--title",default="Imported Markdown"); md.add_argument("--author",default=""); md.add_argument("--language",default="en"); md.add_argument("--output",required=True)
    sm=sub.add_parser("from-summary"); sm.add_argument("input"); sm.add_argument("--output",required=True)
    gh=sub.add_parser("from-github-snapshot"); gh.add_argument("input"); gh.add_argument("--output",required=True)
    pe=sub.add_parser("from-pr-event"); pe.add_argument("input"); pe.add_argument("--output",required=True)
    d=sub.add_parser("delta"); d.add_argument("before"); d.add_argument("after")
    rb=sub.add_parser("rebuild-plan"); rb.add_argument("before"); rb.add_argument("after"); rb.add_argument("--shard-size",type=int,default=128); rb.add_argument("--output")
    pr=sub.add_parser("project"); pr.add_argument("input"); pr.add_argument("--depth",type=int,required=True); pr.add_argument("--output",required=True)
    bd=sub.add_parser("build-depths"); bd.add_argument("input"); bd.add_argument("--depths",type=_depths,default=[0,1,2,3,4,5]); bd.add_argument("--output-dir",default="generated/omega_latex_t/depths")
    nt=sub.add_parser("notation"); nt.add_argument("input"); ev=sub.add_parser("evidence"); ev.add_argument("input"); mr=sub.add_parser("math-render"); mr.add_argument("input"); mr.add_argument("--node-id",required=True); tb=sub.add_parser("theorem-bundle"); tb.add_argument("input"); tb.add_argument("--theorem-id",required=True); tb.add_argument("--output-dir",required=True)
    bib=sub.add_parser("from-bibtex"); bib.add_argument("docir"); bib.add_argument("bibtex"); bib.add_argument("--output",required=True)
    br=sub.add_parser("bibliography"); br.add_argument("input")
    fr=sub.add_parser("figure-render"); fr.add_argument("input"); fr.add_argument("--node-id",required=True)
    ur=sub.add_parser("uncertainty"); ur.add_argument("input"); vr=sub.add_parser("verifier-receipts"); vr.add_argument("input")
    mg=sub.add_parser("metadocument"); mg.add_argument("inputs",nargs="+"); mg.add_argument("--output")
    up=sub.add_parser("universe-plan"); up.add_argument("manifest"); up.add_argument("--output")
    ub=sub.add_parser("build-universe"); ub.add_argument("manifest"); ub.add_argument("--output-dir",default="generated/omega_latex_universe"); ub.add_argument("--cache-dir",default=".omega-latex-universe-cache"); ub.add_argument("--no-resume",action="store_true")
    return p

def main(argv=None):
    args=build_parser().parse_args(argv)
    try:
        if args.command=="from-markdown": _write_docir(markdown_to_document(Path(args.input).read_text(encoding="utf-8"),title=args.title,author=args.author,language=args.language),args.output); return 0
        if args.command=="from-summary": _write_docir(summary_bundle_to_document(json.loads(Path(args.input).read_text(encoding="utf-8"))),args.output); return 0
        if args.command=="from-github-snapshot": _write_docir(github_snapshot_to_document(json.loads(Path(args.input).read_text(encoding="utf-8"))),args.output); return 0
        if args.command=="from-pr-event": _write_docir(github_pr_event_to_document(json.loads(Path(args.input).read_text(encoding="utf-8"))),args.output); return 0
        if args.command=="from-bibtex":
            _write_docir(attach_bibliography(_load(args.docir),parse_bibtex(Path(args.bibtex).read_text(encoding="utf-8"))),args.output); return 0
        if args.command=="bibliography": _write_json(bibliography_report(_load(args.input))); return 0
        if args.command=="uncertainty": _write_json(uncertainty_ledger(_load(args.input))); return 0
        if args.command=="verifier-receipts": _write_json(verifier_receipt_report(_load(args.input))); return 0
        if args.command=="metadocument": _write_json(metadocument_graph({Path(path).stem:_load(path) for path in args.inputs}),args.output); return 0
        if args.command=="universe-plan": _write_json(universe_plan(json.loads(Path(args.manifest).read_text(encoding="utf-8"))),args.output); return 0
        if args.command=="build-universe": _write_json(build_universe(args.manifest,args.output_dir,args.cache_dir,resume=not args.no_resume)); return 0
        if args.command=="delta": _write_json(semantic_delta(_load(args.before),_load(args.after))); return 0
        if args.command=="rebuild-plan": _write_json(rebuild_plan(_load(args.before),_load(args.after),shard_size=args.shard_size),args.output); return 0
        if args.command=="project": _write_docir(project_depth(_load(args.input),args.depth),args.output); return 0
        if args.command=="build-depths":
            doc=_load(args.input); compiler=DocumentCompiler(); out=Path(args.output_dir); manifest={"source_semantic_hash":doc.semantic_hash(),"depths":{}}
            for depth,projection in project_depths(doc,args.depths).items(): manifest["depths"][str(depth)]=compiler.build_to(projection,out/f"D{depth}").manifest()
            out.mkdir(parents=True,exist_ok=True); _write_json(manifest,out/"depth-manifest.json"); print(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)); return 0
        if args.command=="notation": _write_json({"registry":notation_registry(_load(args.input)),"rename_plan":notation_rename_plan(_load(args.input))}); return 0
        if args.command=="evidence": _write_json(evidence_matrix(_load(args.input))); return 0
        if args.command=="math-render":
            doc=_load(args.input); node=next((x for x in doc.nodes if x.id==args.node_id),None)
            if node is None or not node.math_ir: raise ValueError(f"node {args.node_id!r} missing or has no math_ir")
            print(render_math(node.math_ir)); return 0
        if args.command=="figure-render":
            doc=_load(args.input); node=next((x for x in doc.nodes if x.id==args.node_id),None)
            if node is None or not node.figure_ir: raise ValueError(f"node {args.node_id!r} missing or has no figure_ir")
            print(render_figure_ir(node.figure_ir,node_id=node.id,title=node.title)); return 0
        if args.command=="theorem-bundle":
            paths=write_theorem_bundle(_load(args.input),args.theorem_id,args.output_dir); print(json.dumps({k:str(v) for k,v in paths.items()},indent=2,sort_keys=True)); return 0
        doc=_load(args.input)
        if args.command=="audit":
            report=audit_document(doc); _write_json(report.to_mapping()); return 0 if report.passed else 1
        compiler=DocumentCompiler(fail_on_audit_error=not getattr(args,"allow_audit_errors",False))
        if args.command=="render": print(compiler.render(doc).latex,end=""); return 0
        if args.command=="incremental-build":
            force=tuple(semantic_delta(_load(args.before),doc)["affected_after"]) if args.before else (); artifact=compiler.build_incremental_to(doc,args.output_dir,args.cache_dir,force_node_ids=force); _write_json(artifact.manifest()); return 0
        if args.depth is not None: doc=project_depth(doc,args.depth)
        out=Path(args.output_dir); artifact=compiler.build_to(doc,out); _write_json(artifact.manifest()); return _compile_pdf(out,args.engine) if args.pdf else 0
    except (ValueError,KeyError) as exc:
        print(f"omega-doc: {exc}",file=sys.stderr); return 1

if __name__=="__main__": raise SystemExit(main())
