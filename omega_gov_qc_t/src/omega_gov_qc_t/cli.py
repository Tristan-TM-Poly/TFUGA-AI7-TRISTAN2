"""Command-line interface for TristanGovGraph Quebec."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .graph_exports import GraphExporter
from .municipal_report import MunicipalReportBuilder


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-gov-qc",
        description="TristanGovGraph Quebec local demo CLI.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Generate all demo artifacts.")
    demo.add_argument("--out", default="reports/generated", help="Output directory.")

    bundle = sub.add_parser("bundle", help="Generate demo JSON bundle.")
    bundle.add_argument("--out", default="reports/generated/municipal_demo_bundle.json", help="Output JSON path.")

    graphml = sub.add_parser("graphml", help="Generate demo GraphML export.")
    graphml.add_argument("--out", default="reports/generated/municipal_demo.graphml", help="Output GraphML path.")

    report = sub.add_parser("report", help="Generate demo Markdown report.")
    report.add_argument("--out", default="reports/generated/municipal_demo_report.md", help="Output Markdown path.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    artifacts = MunicipalReportBuilder().build_demo()

    if args.command == "demo":
        out_dir = Path(args.out)
        _write_text(out_dir / "municipal_demo_report.md", artifacts.report_markdown)
        _write_text(out_dir / "municipal_demo_bundle.json", artifacts.bundle_json)
        graphml = GraphExporter().to_graphml(artifacts.graph).content
        _write_text(out_dir / "municipal_demo.graphml", graphml)
        return 0

    if args.command == "bundle":
        _write_text(Path(args.out), artifacts.bundle_json)
        return 0

    if args.command == "graphml":
        graphml = GraphExporter().to_graphml(artifacts.graph).content
        _write_text(Path(args.out), graphml)
        return 0

    if args.command == "report":
        _write_text(Path(args.out), artifacts.report_markdown)
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
