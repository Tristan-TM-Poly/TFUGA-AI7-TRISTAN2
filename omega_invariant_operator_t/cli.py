from __future__ import annotations

import argparse
import json

from .tsp import posthoc_exchange_name, synthesize_tsp_exchange


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ω invariant-first operator synthesis R0.1")
    subparsers = parser.add_subparsers(dest="command", required=True)
    tsp = subparsers.add_parser("tsp", help="run the bounded exact TSP pilot")
    tsp.add_argument("--nodes", type=int, default=5, help="number of nodes in canonical cycle")
    tsp.add_argument("--max-candidates", type=int, default=100_000)
    tsp.add_argument("--max-witnesses", type=int, default=16)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "tsp":
        if args.nodes < 3:
            raise SystemExit("--nodes must be >= 3")
        receipt = synthesize_tsp_exchange(
            tuple(range(args.nodes)),
            max_candidates=args.max_candidates,
            max_witnesses=args.max_witnesses,
        )
        payload = receipt.to_dict()
        payload["posthoc_classes"] = sorted({posthoc_exchange_name(w) for w in receipt.witnesses})
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if receipt.status == "PASS" else 2
    raise AssertionError("unreachable")
