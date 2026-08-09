from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .adapters import github_snapshot_to_document, markdown_to_document, summary_bundle_to_document
from .audit import audit_document
from .compiler import DocumentCompiler
from .delta import semantic_delta
from .models import DocumentIR


def _load(path: str) -> DocumentIR:
    return DocumentIR.from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))


def _write_docir(doc: DocumentIR, path: str) -> None:
    Path(path).write_text(json.dumps(doc.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _compile_pdf(out: Path, engine: str) -> int:
    executable = shutil.which(engine)
    if executable is None:
        print(json.dumps({"pdf": "skipped", "reason": f"{engine} not found"})); return 2
    run = subprocess.run([executable, "-interaction=nonstopmode", "-halt-on-error", "document.tex"], cwd=out, capture_output=True, text=True, timeout=120, check=False)
    (out / "latex-build.stdout.log").write_text(run.stdout, encoding="utf-8"); (out / "latex-build.stderr.log").write_text(run.stderr, encoding="utf-8")
    print(json.dumps({"pdf": "passed" if run.returncode == 0 else "failed", "returncode": run.returncode})); return run.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-doc", description="Ω-LATEX-T∞ deterministic evidence-bound document compiler")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Compile a JSON DocumentIR into LaTeX artifacts"); build.add_argument("input"); build.add_argument("--output-dir", default="generated/omega_latex_t"); build.add_argument("--allow-audit-errors", action="store_true"); build.add_argument("--pdf", action="store_true"); build.add_argument("--engine", default="pdflatex", choices=["pdflatex", "xelatex", "lualatex"])
    audit = sub.add_parser("audit", help="Audit a JSON DocumentIR without rendering"); audit.add_argument("input")
    render = sub.add_parser("render", help="Render LaTeX to stdout after OAK audit"); render.add_argument("input")
    md = sub.add_parser("from-markdown", help="Conservatively convert Markdown into DocumentIR"); md.add_argument("input"); md.add_argument("--title", default="Imported Markdown"); md.add_argument("--author", default=""); md.add_argument("--language", default="en"); md.add_argument("--output", required=True)
    summary = sub.add_parser("from-summary", help="Convert an omega_summary_fractal_t SummaryBundle into DocumentIR"); summary.add_argument("input"); summary.add_argument("--output", required=True)
    gh = sub.add_parser("from-github-snapshot", help="Convert an authorized normalized GitHub snapshot JSON into DocumentIR"); gh.add_argument("input"); gh.add_argument("--output", required=True)
    delta = sub.add_parser("delta", help="Compute deterministic DocumentIR semantic delta and rebuild closure"); delta.add_argument("before"); delta.add_argument("after")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "from-markdown":
        _write_docir(markdown_to_document(Path(args.input).read_text(encoding="utf-8"), title=args.title, author=args.author, language=args.language), args.output); return 0
    if args.command == "from-summary":
        _write_docir(summary_bundle_to_document(json.loads(Path(args.input).read_text(encoding="utf-8"))), args.output); return 0
    if args.command == "from-github-snapshot":
        _write_docir(github_snapshot_to_document(json.loads(Path(args.input).read_text(encoding="utf-8"))), args.output); return 0
    if args.command == "delta":
        print(json.dumps(semantic_delta(_load(args.before), _load(args.after)), ensure_ascii=False, indent=2, sort_keys=True)); return 0
    doc = _load(args.input)
    if args.command == "audit":
        report = audit_document(doc); print(json.dumps(report.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True)); return 0 if report.passed else 1
    compiler = DocumentCompiler(fail_on_audit_error=not getattr(args, "allow_audit_errors", False))
    try:
        if args.command == "render": print(compiler.render(doc).latex, end=""); return 0
        out = Path(args.output_dir); artifact = compiler.build_to(doc, out); print(json.dumps(artifact.manifest(), ensure_ascii=False, indent=2, sort_keys=True))
        return _compile_pdf(out, args.engine) if args.pdf else 0
    except ValueError as exc:
        print(f"omega-doc: {exc}", file=sys.stderr); return 1


if __name__ == "__main__": raise SystemExit(main())
