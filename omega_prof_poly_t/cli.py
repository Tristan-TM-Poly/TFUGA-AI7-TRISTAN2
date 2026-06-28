"""Stable CLI for Omega absorb v1.1."""

from __future__ import annotations

import argparse

from .e2e_pipeline_v09 import run_v09_e2e_pipeline
from .export_commands import build_export_payloads
from .release_bundle_writer import write_release_bundle
from .roadmap_compiler import render_roadmap_markdown


VERSION = "1.1.0"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-absorb", description="Omega absorb public research pipeline")
    parser.add_argument(
        "command",
        choices=("version", "demo", "roadmap", "summary-json", "validation-json", "graph-json", "write-bundle"),
        help="Command to run",
    )
    return parser


def run_cli(argv: list[str] | None = None) -> str:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "version":
        return f"omega-absorb {VERSION}\n"
    if args.command in {"summary-json", "validation-json", "graph-json"}:
        payloads = build_export_payloads()
        if args.command == "summary-json":
            return payloads.summary_json
        if args.command == "validation-json":
            return payloads.validation_json
        return payloads.graph_json
    if args.command == "write-bundle":
        result = write_release_bundle()
        return "".join(f"{item.path} {item.bytes_written}\n" for item in result.files)
    result = run_v09_e2e_pipeline()
    if args.command == "roadmap":
        return render_roadmap_markdown(result.roadmap)
    return (
        "Omega absorb demo\n"
        f"validation_clean={result.validation.is_clean}\n"
        f"artifact_count={len(result.artifact_run.manifest.artifacts)}\n"
        f"roadmap_steps={len(result.roadmap.steps)}\n"
    )


def main() -> None:
    print(run_cli().rstrip())


if __name__ == "__main__":
    main()
