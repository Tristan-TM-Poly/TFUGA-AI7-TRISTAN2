from __future__ import annotations

import argparse
import json

from .genesis import mine_graph_problem, synthesize_from_problem
from .tsp import cycle_edges, posthoc_exchange_name, synthesize_tsp_exchange


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ω invariant/operator/problem genesis R0.1→R0.2")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tsp = subparsers.add_parser("tsp", help="run the bounded exact TSP pilot")
    tsp.add_argument("--nodes", type=int, default=5, help="number of nodes in canonical cycle")
    tsp.add_argument("--max-candidates", type=int, default=100_000)
    tsp.add_argument("--max-witnesses", type=int, default=16)

    genesis = subparsers.add_parser(
        "tsp-genesis",
        help="mine graph invariant hypotheses from traces before exact operator synthesis",
    )
    genesis.add_argument("--max-candidates", type=int, default=100_000)
    genesis.add_argument("--max-witnesses", type=int, default=16)
    return parser


def _tsp_genesis_payload(max_candidates: int, max_witnesses: int) -> dict[str, object]:
    nodes = (0, 1, 2, 3, 4)
    training = (
        cycle_edges((0, 1, 2, 3, 4)),
        cycle_edges((0, 1, 3, 4, 2)),
    )
    holdout = (
        cycle_edges((0, 2, 1, 4, 3)),
        cycle_edges((0, 3, 1, 2, 4)),
    )
    problem = mine_graph_problem(nodes, training, holdout)
    receipt = synthesize_from_problem(
        problem,
        max_candidates=max_candidates,
        max_witnesses=max_witnesses,
    )
    result = {
        "problem": problem.to_dict(),
        "synthesis": receipt.to_dict(),
        "posthoc_classes": sorted({posthoc_exchange_name(w) for w in receipt.witnesses}),
    }
    return result


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

    if args.command == "tsp-genesis":
        payload = _tsp_genesis_payload(args.max_candidates, args.max_witnesses)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["synthesis"]["status"] == "PASS" else 2

    raise AssertionError("unreachable")
