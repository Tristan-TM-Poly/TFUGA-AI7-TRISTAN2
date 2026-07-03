"""Command-line interface for Ω-AI-TRISTAN-LAB."""

from __future__ import annotations

import argparse

from .agent_harness import AgentHarness
from .reporting import ReportRenderer
from .workspace import Workspace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Ω-AI-TRISTAN-LAB on one idea or local documents.")
    parser.add_argument("--idea", required=True, help="Raw idea to formalize and evaluate.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    parser.add_argument(
        "--ingest",
        nargs="*",
        default=None,
        help="Optional local document paths to ingest before evaluation. Supports text/Markdown and optional PDF.",
    )
    parser.add_argument(
        "--context-query",
        default=None,
        help="Optional query used to retrieve local context from ingested documents.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Persist report.json, report.md, and manifest.txt under this directory.",
    )
    args = parser.parse_args(argv)

    if args.output_dir:
        workspace = Workspace(args.output_dir)
        if args.ingest:
            run = workspace.run_with_documents(
                idea=args.idea,
                document_paths=args.ingest,
                context_query=args.context_query,
            )
        else:
            run = workspace.run_idea(args.idea)
        print(f"Saved Ω-AI-TRISTAN-LAB run: {run.run_dir}")
        print(f"JSON: {run.json_report}")
        print(f"Markdown: {run.markdown_report}")
        return 0

    if args.ingest:
        report = Workspace("omega_runs").harness.run(
            args.idea + "\n\nNote: --ingest was provided without --output-dir; run again with --output-dir to persist document context."
        )
    else:
        report = AgentHarness().run(args.idea)
    print(ReportRenderer().to_json_text(report, pretty=args.pretty))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
