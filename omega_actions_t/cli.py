"""CLI for Ω-ACTIONS-T∞ static GitHub Actions analysis."""

from __future__ import annotations

import argparse
import json

from .analyzer import render_markdown, write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="omega-actions",
        description="Read-only static optimizer for GitHub Actions workflows.",
    )
    parser.add_argument("--root", default=".", help="Repository root to analyze")
    parser.add_argument("--json-out", help="Optional JSON report path")
    parser.add_argument("--markdown-out", help="Optional Markdown report path")
    parser.add_argument(
        "--format",
        choices=("summary", "json", "markdown"),
        default="summary",
        help="Stdout format",
    )
    args = parser.parse_args(argv)

    report = write_report(args.root, json_out=args.json_out, markdown_out=args.markdown_out)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(report), end="")
    else:
        aggregate = report["aggregate"]
        print(
            "Ω-ACTIONS-T∞ "
            f"workflows={aggregate['workflow_count']} "
            f"jobs={aggregate['job_count']} "
            f"depth={aggregate['max_structural_depth']} "
            f"efficiency_proxy={aggregate['static_efficiency_score']}/100 "
            f"recommendations={aggregate['recommendation_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
