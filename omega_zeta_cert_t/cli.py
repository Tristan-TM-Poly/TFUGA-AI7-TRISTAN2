from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .core import classify_frontier, compile_problem_cells, effective_rank_diagnostic, rank_routes
from .presets import default_bundle


def _jsonable(value):
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def cmd_frontier(args: argparse.Namespace) -> int:
    bundle = default_bundle(args.target)
    decision = classify_frontier(bundle.family, args.target, moment_spec=bundle.moment_spec)
    payload = _jsonable(asdict(decision))
    payload["family_headroom"] = bundle.family.headroom
    payload["rh_solved_claimed"] = False
    payload["proof_claimed"] = False
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_routes(args: argparse.Namespace) -> int:
    bundle = default_bundle(args.target)
    rows = [
        {
            "route_id": route.route_id,
            "title": route.title,
            "voi_score": route.voi_score,
            "barrier_target": route.barrier_target.value,
        }
        for route in rank_routes(bundle.routes)
    ]
    print(json.dumps(rows, indent=2, sort_keys=True))
    return 0


def cmd_cells(args: argparse.Namespace) -> int:
    bundle = default_bundle(args.target)
    rows = compile_problem_cells(bundle)
    text = "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def cmd_effective_rank(args: argparse.Namespace) -> int:
    value = effective_rank_diagnostic(args.trace, args.frobenius_sq)
    print(json.dumps({
        "effective_rank_diagnostic": value,
        "rank_lower_bound_claimed": False,
        "zeta_theorem_claimed": False,
    }, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-zeta-cert")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("frontier", help="classify a target against a declared certificate-family ceiling")
    p.add_argument("--target", type=float, default=0.70)
    p.set_defaults(func=cmd_frontier)

    p = sub.add_parser("routes", help="rank bounded research routes by heuristic value of information")
    p.add_argument("--target", type=float, default=0.70)
    p.set_defaults(func=cmd_routes)

    p = sub.add_parser("cells", help="emit R0.10-compatible Problem Atlas cells as JSONL")
    p.add_argument("--target", type=float, default=0.70)
    p.add_argument("--output")
    p.set_defaults(func=cmd_cells)

    p = sub.add_parser("effective-rank", help="generic spectral concentration diagnostic")
    p.add_argument("--trace", type=float, required=True)
    p.add_argument("--frobenius-sq", type=float, required=True)
    p.set_defaults(func=cmd_effective_rank)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
