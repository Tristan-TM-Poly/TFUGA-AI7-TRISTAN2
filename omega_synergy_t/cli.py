"""Command-line interface for Ω-SYNERGY-T∞ Foundry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .discovery import closure_bridges, discover_n_order, select_portfolio
from .reporting import write_foundry_bundle
from .scanner import ScannerPolicy, scan_repositories


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ω-SYNERGY-T∞ review-only discovery and experiment compiler")
    parser.add_argument("--repo-root", action="append", dest="roots", help="Repository root; repeat for multi-repository analysis")
    parser.add_argument("--out", default="reports/github-autonomous-reactor/synergy-foundry")
    parser.add_argument("--max-order", type=int, default=4)
    parser.add_argument("--beam-width", type=int, default=96)
    parser.add_argument("--top-k", type=int, default=25)
    parser.add_argument("--max-nodes", type=int, default=800)
    parser.add_argument("--portfolio-budget", type=float, default=4.0)
    parser.add_argument("--closure-threshold", type=float, default=0.35)
    return parser


def run(args: argparse.Namespace) -> dict:
    if not 2 <= args.max_order <= 8:
        raise ValueError("max-order must be between 2 and 8")
    if args.beam_width < args.top_k or args.top_k < 1:
        raise ValueError("require beam-width >= top-k >= 1")
    roots = [Path(value).resolve() for value in (args.roots or ["."]) if Path(value).exists()]
    if not roots:
        raise ValueError("at least one repository root must exist")
    scan = scan_repositories(roots, ScannerPolicy(max_nodes=args.max_nodes))
    candidates = discover_n_order(scan.creations, scan.file_systems, args.max_order, args.beam_width, args.top_k)
    all_candidates = [candidate for order in sorted(candidates) for candidate in candidates[order]]
    portfolio = select_portfolio(all_candidates, args.portfolio_budget)
    bridges = closure_bridges(scan.creations, args.closure_threshold)
    out = roots[0] / args.out
    report = write_foundry_bundle(
        out,
        roots,
        scan.creations,
        candidates,
        {
            "max_order": args.max_order,
            "beam_width": args.beam_width,
            "top_k": args.top_k,
            "max_nodes": args.max_nodes,
            "portfolio_budget": args.portfolio_budget,
            "closure_threshold": args.closure_threshold,
        },
        scan.diagnostics,
    )
    (out / "closure_bridges.json").write_text(json.dumps([item.to_dict() for item in bridges], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "portfolio.json").write_text(json.dumps([item.to_dict() for item in portfolio], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {**report["counts"], "closure_bridges": len(bridges), "portfolio": len(portfolio), "out": str(out)}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        summary = run(args)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
