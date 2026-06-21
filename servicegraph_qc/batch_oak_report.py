#!/usr/bin/env python3
"""Batch OAK reporting for ServiceGraph-QC examples.

Produces a compact Markdown table from a folder of ServiceGraph YAML files.
Uses only the Python standard library.
"""

from __future__ import annotations

import sys
from pathlib import Path
from oak_service_meter import parse_simple_yaml, score_service


def markdown_row(values: list[object]) -> str:
    return "| " + " | ".join(str(v) for v in values) + " |"


def main(argv: list[str]) -> int:
    folder = Path(argv[1]) if len(argv) > 1 else Path(__file__).parent / "examples"
    if not folder.exists() or not folder.is_dir():
        print(f"Examples folder not found: {folder}", file=sys.stderr)
        return 2

    reports = []
    for path in sorted(folder.glob("*.yaml")):
        data = parse_simple_yaml(path)
        report = score_service(data)
        reports.append((path.name, data, report))

    if not reports:
        print(f"No .yaml files found in {folder}", file=sys.stderr)
        return 1

    print("# ServiceGraph-QC — Batch OAK Report")
    print()
    print(markdown_row(["file", "service", "score", "level", "top_penalty", "next_oak_test"]))
    print(markdown_row(["---", "---", "---:", "---", "---", "---"]))

    for filename, data, report in reports:
        penalties = report["penalties"]
        top_penalty = max(penalties.items(), key=lambda item: item[1])[0] if penalties else "none"
        tests = data.get("oak_tests", [])
        next_test = tests[0] if tests else "add OAK tests"
        print(
            markdown_row(
                [
                    filename,
                    report["service_name"],
                    report["oak_score"],
                    report["maturity_level"],
                    top_penalty,
                    next_test,
                ]
            )
        )

    print()
    print("## OAK-safe interpretation")
    print("Scores are diagnostic signals. They are not official performance claims, public decisions, or legal conclusions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
