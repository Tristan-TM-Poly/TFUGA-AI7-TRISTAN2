from __future__ import annotations

import argparse
import json
import sys

from .conflicts import EvidenceConflictEngine
from .debt import ProofDebtEngine
from .experiments import ExperimentAllocator, candidates_from_mapping
from .graph import EpistemicGraphEngine
from .io import read_json, write_json
from .oak import run_oakbench
from .slo import TruthSLOEngine, slos_from_mapping


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-ci-proof-r03", description="Ω-CI R0.3 epistemic graph, proof debt and Truth SLOs")
    sub = parser.add_subparsers(dest="command", required=True)
    graph = sub.add_parser("graph")
    graph.add_argument("--graph", required=True)
    graph.add_argument("--output")
    inv = sub.add_parser("invalidate")
    inv.add_argument("--graph", required=True)
    inv.add_argument("--changed", action="append", required=True)
    inv.add_argument("--output", required=True)
    debt = sub.add_parser("debt")
    debt.add_argument("--graph", required=True)
    debt.add_argument("--state", required=True)
    debt.add_argument("--output", required=True)
    slo = sub.add_parser("slo")
    slo.add_argument("--graph", required=True)
    slo.add_argument("--state", required=True)
    slo.add_argument("--slos", required=True)
    slo.add_argument("--output", required=True)
    conflicts = sub.add_parser("conflicts")
    conflicts.add_argument("--graph", required=True)
    conflicts.add_argument("--output", required=True)
    exp = sub.add_parser("experiments")
    exp.add_argument("--candidates", required=True)
    exp.add_argument("--budget", required=True, type=float)
    exp.add_argument("--output", required=True)
    sub.add_parser("oak")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "graph":
        engine = EpistemicGraphEngine.from_mapping(read_json(args.graph))
        payload = {"graph": engine.graph.to_dict(), "stats": engine.stats()}
        if args.output: write_json(args.output, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.command == "invalidate":
        engine = EpistemicGraphEngine.from_mapping(read_json(args.graph))
        result = engine.invalidate(args.changed)
        write_json(args.output, result.to_dict())
        print(result.result_id)
        return 0
    if args.command == "debt":
        engine = EpistemicGraphEngine.from_mapping(read_json(args.graph))
        report = ProofDebtEngine().evaluate(engine, read_json(args.state))
        write_json(args.output, report.to_dict())
        print(report.report_id)
        return 0
    if args.command == "slo":
        engine = EpistemicGraphEngine.from_mapping(read_json(args.graph))
        state = read_json(args.state)
        debt = ProofDebtEngine().evaluate(engine, state)
        report = TruthSLOEngine().evaluate(engine, state, debt, slos_from_mapping(read_json(args.slos)))
        write_json(args.output, report.to_dict())
        print(report.report_id)
        return 0 if report.passed else 2
    if args.command == "conflicts":
        engine = EpistemicGraphEngine.from_mapping(read_json(args.graph))
        report = EvidenceConflictEngine().analyze(engine)
        write_json(args.output, report.to_dict())
        print(report.report_id)
        return 0
    if args.command == "experiments":
        portfolio = ExperimentAllocator().allocate(candidates_from_mapping(read_json(args.candidates)), budget=args.budget)
        write_json(args.output, portfolio.to_dict())
        print(portfolio.portfolio_id)
        return 0
    if args.command == "oak":
        payload = run_oakbench()
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["passed"] else 1
    raise AssertionError("unreachable")


if __name__ == "__main__":
    sys.exit(main())
