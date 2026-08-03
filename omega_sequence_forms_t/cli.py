"""Command line interface for Ω-SUITE-FORM-T∞ R0.1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .discover import discover_forms
from .models import CandidateKind


def _parse_terms(text: str) -> list[str]:
    terms = [item.strip() for item in text.split(",") if item.strip()]
    if not terms:
        raise argparse.ArgumentTypeError("provide comma-separated terms")
    return terms


def benchmark_payload() -> dict[str, Any]:
    fixtures = [
        {
            "name": "cubic_shifted",
            "terms": [1, 8, 27, 64, 125, 216, 343, 512, 729],
            "required": CandidateKind.NEWTON_POLYNOMIAL,
            "next_index": 9,
            "next_value": 1000,
        },
        {
            "name": "fibonacci",
            "terms": [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89],
            "required": CandidateKind.LINEAR_RECURRENCE,
            "next_index": 12,
            "next_value": 144,
        },
        {
            "name": "geometric",
            "terms": [3, 6, 12, 24, 48, 96, 192, 384],
            "required": CandidateKind.RATIONAL_GENERATING_FUNCTION,
            "next_index": 8,
            "next_value": 768,
        },
    ]
    results: list[dict[str, Any]] = []
    for fixture in fixtures:
        report = discover_forms(fixture["terms"])
        matching = [candidate for candidate in report.candidates if candidate.kind == fixture["required"]]
        predicted = None if not matching else matching[0].evaluate(fixture["next_index"])
        passed = predicted == fixture["next_value"]
        results.append({
            "name": fixture["name"],
            "required_kind": fixture["required"].value,
            "predicted_next": None if predicted is None else str(predicted),
            "expected_next": str(fixture["next_value"]),
            "passed": passed,
            "candidate_count": len(report.candidates),
        })
    return {
        "schema": "omega-sequence-forms-benchmark/1",
        "fixtures": results,
        "passed": all(item["passed"] for item in results),
        "global_identity_proved": False,
        "status": "OAK_SOFTWARE_FIXTURES_ONLY",
    }


def demo_payload(name: str) -> dict[str, Any]:
    demos = {
        "fibonacci": [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89],
        "cubes": [1, 8, 27, 64, 125, 216, 343, 512, 729],
        "geometric": [3, 6, 12, 24, 48, 96, 192, 384],
    }
    return discover_forms(demos[name]).to_dict()


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="omega-sequence-forms",
        description="Discover exact candidate forms for finite mathematical sequences.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover")
    discover.add_argument("terms", type=_parse_terms, help="comma-separated integers, decimals or fractions")
    discover.add_argument("--holdout", type=int)
    discover.add_argument("--max-degree", type=int, default=12)
    discover.add_argument("--max-order", type=int, default=12)
    discover.add_argument("--output")

    demo = subparsers.add_parser("demo")
    demo.add_argument("name", choices=("fibonacci", "cubes", "geometric"))
    demo.add_argument("--output")

    benchmark = subparsers.add_parser("benchmark")
    benchmark.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "discover":
        payload = discover_forms(
            args.terms,
            holdout=args.holdout,
            max_degree=args.max_degree,
            max_order=args.max_order,
        ).to_dict()
    elif args.command == "demo":
        payload = demo_payload(args.name)
    elif args.command == "benchmark":
        payload = benchmark_payload()
    else:  # pragma: no cover
        parser.error("unknown command")
        return 2

    _write(payload, args.output)
    return 0 if payload.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
