"""Command line interface for Ω-ORG-FAM-T R0.3 Evidence Engine."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .evidence_benchmark import audit_benchmark, generate_benchmark
from .evidence_ledger import read_events, verify_events
from .formula import Species, balance_reaction, parse_formula
from .mixture import fit_nonnegative_mixture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="omega-organic-evidence")
    sub = parser.add_subparsers(dest="command", required=True)
    formula = sub.add_parser("parse-formula")
    formula.add_argument("formula")
    balance = sub.add_parser("balance")
    balance.add_argument("--reactants", nargs="+", required=True)
    balance.add_argument("--products", nargs="+", required=True)
    ledger = sub.add_parser("verify-ledger")
    ledger.add_argument("path", type=Path)
    bench = sub.add_parser("benchmark")
    bench.add_argument("--root", type=Path, default=Path("."))
    bench.add_argument("--cases", type=int, default=8_388_608)
    bench.add_argument("--shard-cases", type=int, default=524_288)
    bench.add_argument("--clean", action="store_true")
    audit = sub.add_parser("audit-benchmark")
    audit.add_argument("path", type=Path)
    mix = sub.add_parser("mixture-demo")
    mix.add_argument("--observed", nargs="+", type=float, required=True)
    args = parser.parse_args(argv)
    if args.command == "parse-formula":
        result = parse_formula(args.formula)
    elif args.command == "balance":
        left, right = balance_reaction(tuple(Species(item) for item in args.reactants), tuple(Species(item) for item in args.products))
        result = {"reactants": dict(zip(args.reactants, left, strict=True)), "products": dict(zip(args.products, right, strict=True)), "oak_boundary": "balanced does not mean feasible or safe"}
    elif args.command == "verify-ledger":
        result = verify_events(read_events(args.path))
    elif args.command == "benchmark":
        result = generate_benchmark(args.root, cases=args.cases, shard_cases=args.shard_cases, clean=args.clean)
    elif args.command == "audit-benchmark":
        result = audit_benchmark(args.path)
    elif args.command == "mixture-demo":
        dimension = len(args.observed)
        references = {"left": [1.0 if i < dimension // 2 else 0.0 for i in range(dimension)], "right": [0.0 if i < dimension // 2 else 1.0 for i in range(dimension)]}
        result = asdict(fit_nonnegative_mixture(args.observed, references))
    else:
        parser.error("unknown command")
    print(json.dumps(result, indent=2, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
