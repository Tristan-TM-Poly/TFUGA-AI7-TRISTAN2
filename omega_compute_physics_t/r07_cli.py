"""Static/planning CLI for Omega Optimization Foundry R0.7."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .opportunity_engine import OpportunityEvidence, score_optimization_opportunity
from .optimization_credit import shapley_optimization_credit
from .optimization_portfolio import PortfolioOpportunity, optimize_portfolio


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _cmd_opportunity(args: argparse.Namespace) -> int:
    payload = _load_json(args.input)
    row = OpportunityEvidence(**payload)
    print(json.dumps(score_optimization_opportunity(row).to_dict(), indent=2, sort_keys=True))
    return 0


def _cmd_portfolio(args: argparse.Namespace) -> int:
    payload = _load_json(args.input)
    opportunities = tuple(PortfolioOpportunity(**row) for row in payload["opportunities"])
    interactions: dict[tuple[str, str], float] = {}
    for row in payload.get("interactions", []):
        interactions[(str(row["a"]), str(row["b"]))] = float(row["value"])
    report = optimize_portfolio(
        opportunities,
        effort_budget=float(payload["effort_budget"]),
        interactions=interactions,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0


def _cmd_credit(args: argparse.Namespace) -> int:
    payload = _load_json(args.input)
    transformations = tuple(str(item) for item in payload["transformations"])
    coalition_values = {
        frozenset(str(item) for item in row["coalition"]): float(row["value"])
        for row in payload["coalition_values"]
    }
    rows = shapley_optimization_credit(transformations, coalition_values)
    print(json.dumps([row.to_dict() for row in rows], indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-compute-r07")
    sub = parser.add_subparsers(dest="command", required=True)

    opportunity = sub.add_parser("opportunity", help="score one optimization opportunity JSON")
    opportunity.add_argument("input")
    opportunity.set_defaults(func=_cmd_opportunity)

    portfolio = sub.add_parser("portfolio", help="solve a bounded optimization portfolio JSON")
    portfolio.add_argument("input")
    portfolio.set_defaults(func=_cmd_portfolio)

    credit = sub.add_parser("credit", help="compute exact small-N Shapley credit from ablation JSON")
    credit.add_argument("input")
    credit.set_defaults(func=_cmd_credit)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
