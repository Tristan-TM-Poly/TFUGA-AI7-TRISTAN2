"""CLI for OAK-safe InfrastructureGraph Quebec demo artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from .demo_builder import build_demo_artifacts


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-infra-qc", description="OAK-safe InfrastructureGraph Quebec demo CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="Generate demo report and JSON bundle")
    demo.add_argument("--out", default="reports/generated/omega_infra_qc", help="Output directory")

    report = sub.add_parser("report", help="Generate demo Markdown report")
    report.add_argument("--out", default="reports/generated/infra_qc_demo_report.md", help="Output Markdown path")

    bundle = sub.add_parser("bundle", help="Generate demo JSON bundle")
    bundle.add_argument("--out", default="reports/generated/infra_qc_demo_bundle.json", help="Output JSON path")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifacts = build_demo_artifacts()

    if args.command == "demo":
        out = Path(args.out)
        _write_text(out / "infra_qc_demo_report.md", artifacts.report_markdown)
        _write_text(out / "infra_qc_demo_bundle.json", artifacts.bundle_json)
        return 0
    if args.command == "report":
        _write_text(Path(args.out), artifacts.report_markdown)
        return 0
    if args.command == "bundle":
        _write_text(Path(args.out), artifacts.bundle_json)
        return 0
    raise AssertionError(f"unknown command: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
