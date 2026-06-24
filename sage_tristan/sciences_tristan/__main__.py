"""Command line interface for Ω-ST executable core.

Examples:
    python -m sage_tristan.sciences_tristan rank examples/sciences_tristan_seed.json
    python -m sage_tristan.sciences_tristan review examples/sciences_tristan_seed.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ait_oak import AITOAK
from .bayes_tristan_engine import BayesTristanEngine


def _load_engine(path: str) -> BayesTristanEngine:
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        return BayesTristanEngine.from_json_path(path)
    if suffix in {".yaml", ".yml"}:
        return BayesTristanEngine.from_yaml_path(path)
    raise SystemExit(f"Unsupported file type {suffix!r}; use .json or .yaml")


def cmd_rank(args: argparse.Namespace) -> int:
    engine = _load_engine(args.path)
    report = engine.portfolio_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    engine = _load_engine(args.path)
    reviewer = AITOAK()
    reviews = [reviewer.review(card).as_dict() for card in engine.top(args.limit)]
    print(json.dumps({"reviews": reviews}, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ω-ST Sciences de Tristan CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    rank = sub.add_parser("rank", help="Rank science cards with Bayes-Tristan")
    rank.add_argument("path", help="Path to JSON or YAML card portfolio")
    rank.set_defaults(func=cmd_rank)

    review = sub.add_parser("review", help="Generate AIT-OAK reviews for top cards")
    review.add_argument("path", help="Path to JSON or YAML card portfolio")
    review.add_argument("--limit", type=int, default=10)
    review.set_defaults(func=cmd_review)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
