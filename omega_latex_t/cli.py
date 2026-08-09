from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .adapters import (
    github_pr_event_to_document,
    github_snapshot_to_document,
    markdown_to_document,
    summary_bundle_to_document,
)
from .audit import audit_document
from .compiler import DocumentCompiler
from .delta import semantic_delta
from .evidence import evidence_matrix
from .incremental import rebuild_plan
from .math_ir import render_math
from .models import DocumentIR
from .notation import notation_registry, notation_rename_plan
from .projection import project_depth, project_depths
from .theorem_bundle import write_theorem_bundle


def _load(path: str) -> DocumentIR:
    return DocumentIR.from_mapping(json.loads(Path(path).read_text(encoding="utf-8")))


def _write_docir(doc: DocumentIR, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(doc.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _compile_pdf(out: Path, engine: str) -> int:
    executable = shutil.which(engine)
    if executable is None:
        print(json.dumps({"pdf": "skipped", "reason": f"{engine} not found"}))
        return 2
    run = subprocess.run(
        [executable, "-interaction=nonstopmode", "-halt-on-error", "document.tex"],
        cwd=out,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    (out / "latex-build.stdout.log").write_text(run.stdout, encoding="utf-8")
    (out / "latex-build.stderr.log").write_text(run.stderr, encoding="utf-8")
    print(
        json.dumps(
            {"pdf": "passed" if run.returncode == 0 else "failed", "returncode": run.returncode}
        )
    )
    return run.returncode


def _depths(value: str) -> list[int]:
    items = []
    for part in value.split(","):
        text = part.strip()
        if text:
            items.append(int(text))
    if not items:
        raise argparse.ArgumentTypeError("at least one depth is required")
    if any(x < 0 for x in items):
        raise argparse.ArgumentTypeError("depths must be >= 0")
    return items


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-doc",
        description="Ω-LATEX-T∞ deterministic evidence-bound document compiler",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Compile a JSON DocumentIR into LaTeX artifacts")
    build.add_argument("input")
    build.add_argument("--output-dir", default="generated/omega_latex_t")
    build.add_argument("--allow-audit-errors", action="store_true")
    build.add_argument("--pdf", action="store_true")
    build.add_argument("--engine", default="pdflatex", choices=["pdflatex", "xelatex", "lualatex"])
    build.add_argument("--depth", type=int)

    inc = sub.add_parser("incremental-build", help="Build using content-addressed node-fragment cache")
    inc.add_argument("input")
    inc.add_argument("--output-dir", default="generated/omega_latex_t/incremental")
    inc.add_argument("--cache-dir", default=".omega-latex-cache")
    inc.add_argument("--before", help="Optional previous DocumentIR used to force the affected ΔK→ΔD closure")
    inc.add_argument("--allow-audit-errors", action="store_true")

    audit = sub.add_parser("audit", help="Audit a JSON DocumentIR without rendering")
    audit.add_argument("input")

    render = sub.add_parser("render", help="Render LaTeX to stdout after OAK audit")
    render.add_argument("input")

    md = sub.add_parser("from-markdown", help="Conservatively convert Markdown into DocumentIR")
    md.add_argument("input")
    md.add_argument("--title", default="Imported Markdown")
    md.add_argument("--author", default="")
    md.add_argument("--language", default="en")
    md.add_argument("--output", required=True)

    summary = sub.add_parser(
        "from-summary",
        help="Convert an omega_summary_fractal_t SummaryBundle into DocumentIR",
    )
    summary.add_argument("input")
    summary.add_argument("--output", required=True)

    gh = sub.add_parser(
        "from-github-snapshot",
        help="Convert an authorized normalized GitHub snapshot JSON into DocumentIR",
    )
    gh.add_argument("input")
    gh.add_argument("--output", required=True)

    pr_event = sub.add_parser(
        "from-pr-event",
        help="Convert an already-received GitHub pull_request event payload into DocumentIR",
    )
    pr_event.add_argument("input")
    pr_event.add_argument("--output", required=True)

    delta = sub.add_parser(
        "delta",
        help="Compute deterministic DocumentIR semantic delta and rebuild closure",
    )
    delta.add_argument("before")
    delta.add_argument("after")

    rebuild = sub.add_parser(
        "rebuild-plan",
        help="Emit sharded/checkpointed ΔK→ΔD rebuild plan",
    )
    rebuild.add_argument("before")
    rebuild.add_argument("after")
    rebuild.add_argument("--shard-size", type=int, default=128)
    rebuild.add_argument("--output")

    project = sub.add_parser("project", help="Project a DocumentIR to one fractal depth")
    project.add_argument("input")
    project.add_argument("--depth", type=int, required=True)
    project.add_argument("--output", required=True)

    all_depths = sub.add_parser("build-depths", help="Build multiple D^n projections")
    all_depths.add_argument("input")
    all_depths.add_argument("--depths", type=_depths, default=[0, 1, 2, 3, 4, 5])
    all_depths.add_argument("--output-dir", default="generated/omega_latex_t/depths")

    notation = sub.add_parser("notation", help="Emit notation registry and rename-plan")
    notation.add_argument("input")

    evidence = sub.add_parser("evidence", help="Emit claim/source/dependency evidence matrix")
    evidence.add_argument("input")

    math = sub.add_parser("math-render", help="Render structured math_ir for one equation node")
    math.add_argument("input")
    math.add_argument("--node-id", required=True)

    theorem = sub.add_parser(
        "theorem-bundle",
        help="Project one theorem-like node into LaTeX/formal-stub/proof-graph contracts",
    )
    theorem.add_argument("input")
    theorem.add_argument("--theorem-id", required=True)
    theorem.add_argument("--output-dir", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "from-markdown":
        _write_docir(
            markdown_to_document(
                Path(args.input).read_text(encoding="utf-8"),
                title=args.title,
                author=args.author,
                language=args.language,
            ),
            args.output,
        )
        return 0

    if args.command == "from-summary":
        _write_docir(
            summary_bundle_to_document(json.loads(Path(args.input).read_text(encoding="utf-8"))),
            args.output,
        )
        return 0

    if args.command == "from-github-snapshot":
        _write_docir(
            github_snapshot_to_document(json.loads(Path(args.input).read_text(encoding="utf-8"))),
            args.output,
        )
        return 0

    if args.command == "from-pr-event":
        _write_docir(
            github_pr_event_to_document(json.loads(Path(args.input).read_text(encoding="utf-8"))),
            args.output,
        )
        return 0

    if args.command == "delta":
        print(
            json.dumps(
                semantic_delta(_load(args.before), _load(args.after)),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "rebuild-plan":
        payload = rebuild_plan(_load(args.before), _load(args.after), shard_size=args.shard_size)
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.output:
            Path(args.output).write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0

    if args.command == "project":
        _write_docir(project_depth(_load(args.input), args.depth), args.output)
        return 0

    if args.command == "build-depths":
        doc = _load(args.input)
        compiler = DocumentCompiler()
        out = Path(args.output_dir)
        manifest = {"source_semantic_hash": doc.semantic_hash(), "depths": {}}
        for depth, projection in project_depths(doc, args.depths).items():
            artifact = compiler.build_to(projection, out / f"D{depth}")
            manifest["depths"][str(depth)] = artifact.manifest()
        out.mkdir(parents=True, exist_ok=True)
        (out / "depth-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.command == "notation":
        doc = _load(args.input)
        print(
            json.dumps(
                {
                    "registry": notation_registry(doc),
                    "rename_plan": notation_rename_plan(doc),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "evidence":
        print(
            json.dumps(
                evidence_matrix(_load(args.input)),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if args.command == "math-render":
        doc = _load(args.input)
        node = next((x for x in doc.nodes if x.id == args.node_id), None)
        if node is None:
            print(f"omega-doc: unknown node {args.node_id!r}", file=sys.stderr)
            return 1
        if not node.math_ir:
            print(f"omega-doc: node {args.node_id!r} has no math_ir", file=sys.stderr)
            return 1
        print(render_math(node.math_ir))
        return 0

    if args.command == "theorem-bundle":
        try:
            paths = write_theorem_bundle(_load(args.input), args.theorem_id, args.output_dir)
        except (KeyError, ValueError) as exc:
            print(f"omega-doc: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({key: str(path) for key, path in paths.items()}, indent=2, sort_keys=True))
        return 0

    doc = _load(args.input)

    if args.command == "audit":
        report = audit_document(doc)
        print(json.dumps(report.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report.passed else 1

    compiler = DocumentCompiler(
        fail_on_audit_error=not getattr(args, "allow_audit_errors", False)
    )
    try:
        if args.command == "render":
            print(compiler.render(doc).latex, end="")
            return 0

        if args.command == "incremental-build":
            force: tuple[str, ...] = ()
            if args.before:
                delta = semantic_delta(_load(args.before), doc)
                force = tuple(delta["affected_after"])
            artifact = compiler.build_incremental_to(
                doc,
                args.output_dir,
                args.cache_dir,
                force_node_ids=force,
            )
            print(json.dumps(artifact.manifest(), ensure_ascii=False, indent=2, sort_keys=True))
            return 0

        if args.depth is not None:
            doc = project_depth(doc, args.depth)
        out = Path(args.output_dir)
        artifact = compiler.build_to(doc, out)
        print(json.dumps(artifact.manifest(), ensure_ascii=False, indent=2, sort_keys=True))
        return _compile_pdf(out, args.engine) if args.pdf else 0
    except ValueError as exc:
        print(f"omega-doc: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
