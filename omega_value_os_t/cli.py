"""Command-line interface for Ω-VALUE-OS-T∞ R0.1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .constitution import constitution_payload
from .engine import dump_json, evaluate_case, evaluate_portfolio, oak_report
from .fixtures import demo_cases
from .models import ValueCase


def _read_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(payload: object, output: str | None) -> None:
    text = dump_json(payload)
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-value-os", description="Ω-VALUE-OS-T∞ R0.1 review-only judiciary")
    sub = parser.add_subparsers(dest="command", required=True)

    constitution = sub.add_parser("constitution", help="emit the versioned value constitution")
    constitution.add_argument("--output")

    oak = sub.add_parser("oak", help="emit the OAK authority and invariant report")
    oak.add_argument("--output")

    demo = sub.add_parser("demo", help="evaluate deterministic positive, abstain and blocked fixtures")
    demo.add_argument("--output")

    evaluate = sub.add_parser("evaluate", help="evaluate one ValueCase JSON object")
    evaluate.add_argument("input")
    evaluate.add_argument("--output")

    portfolio = sub.add_parser("portfolio", help="evaluate a JSON array of ValueCase objects")
    portfolio.add_argument("input")
    portfolio.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "constitution":
            _write(constitution_payload(), args.output)
        elif args.command == "oak":
            _write(oak_report(), args.output)
        elif args.command == "demo":
            _write(evaluate_portfolio(demo_cases()), args.output)
        elif args.command == "evaluate":
            payload = _read_json(args.input)
            if not isinstance(payload, dict):
                raise ValueError("evaluate input must be a JSON object")
            _write(evaluate_case(ValueCase.from_dict(payload)).payload(), args.output)
        elif args.command == "portfolio":
            payload = _read_json(args.input)
            if not isinstance(payload, list):
                raise ValueError("portfolio input must be a JSON array")
            _write(evaluate_portfolio(ValueCase.from_dict(item) for item in payload), args.output)
        else:  # pragma: no cover
            raise AssertionError(args.command)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"omega-value-os: {exc}\n")
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
