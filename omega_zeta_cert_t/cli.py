from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .core import classify_frontier, compile_problem_cells, effective_rank_diagnostic, rank_routes
from .debt import DualSensitivity, compile_support_debt, compile_theorem_obligations
from .dual import synthetic_dual_fixture
from .formal import build_finite_certificate_theorem_spec
from .moments import moment_coordinate_labels, noncommutative_trace_countermodel
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


def cmd_moments(args: argparse.Namespace) -> int:
    bundle = default_bundle(args.target)
    spec = bundle.moment_spec
    assert spec is not None
    payload = {
        "word_mode": spec.word_mode.value,
        "max_order": spec.max_order,
        "window_count": spec.window_count,
        "order_counts": list(spec.order_counts),
        "observable_count": spec.observable_count,
        "conservative_support_radius": spec.conservative_support_radius,
        "labels": list(moment_coordinate_labels(spec)) if args.labels else None,
        "proof_claimed": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_debt(args: argparse.Namespace) -> int:
    bundle = default_bundle(args.target)
    support_rows = []
    if bundle.moment_spec is not None:
        support_rows = [
            row.to_dict()
            for row in compile_support_debt(
                bundle.moment_spec,
                declared_known_radius=bundle.family.fourier_support_radius,
            )
        ]
    obligations = [
        row.to_dict()
        for row in compile_theorem_obligations(
            bundle.family,
            bundle.target_bound,
            bundle.moment_spec,
        )
    ]
    print(json.dumps({
        "target_bound": bundle.target_bound,
        "support_debt": support_rows,
        "theorem_obligations": obligations,
        "rh_solved_claimed": False,
        "proof_claimed": False,
    }, indent=2, sort_keys=True))
    return 0


def cmd_countermodel(args: argparse.Namespace) -> int:
    print(json.dumps(noncommutative_trace_countermodel().to_dict(), indent=2, sort_keys=True))
    return 0


def cmd_shadow_voi(args: argparse.Namespace) -> int:
    item = DualSensitivity(
        observable_id=args.observable,
        dual_multiplier=args.multiplier,
        anticipated_observable_improvement=args.delta,
        theorem_cost=args.cost,
        source_class=args.source_class,
    )
    print(json.dumps(item.to_dict(), indent=2, sort_keys=True))
    return 0


def cmd_dual_fixture(args: argparse.Namespace) -> int:
    fixture = synthetic_dual_fixture()
    print(json.dumps(fixture.to_dict(), indent=2, sort_keys=True))
    return 0


def cmd_formal_spec(args: argparse.Namespace) -> int:
    fixture = synthetic_dual_fixture()
    spec = build_finite_certificate_theorem_spec(fixture)
    print(json.dumps(spec.to_dict(), indent=2, sort_keys=True))
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

    p = sub.add_parser("moments", help="inspect the moment-word representation and compression contract")
    p.add_argument("--target", type=float, default=0.70)
    p.add_argument("--labels", action="store_true")
    p.set_defaults(func=cmd_moments)

    p = sub.add_parser("debt", help="compile Fourier-support and theorem obligations for a target")
    p.add_argument("--target", type=float, default=0.70)
    p.set_defaults(func=cmd_debt)

    p = sub.add_parser("countermodel", help="run the exact noncommutative trace-word countermodel")
    p.set_defaults(func=cmd_countermodel)

    p = sub.add_parser("shadow-voi", help="score a caller-supplied dual sensitivity without inventing a multiplier")
    p.add_argument("--observable", required=True)
    p.add_argument("--multiplier", type=float, required=True)
    p.add_argument("--delta", type=float, required=True)
    p.add_argument("--cost", type=float, required=True)
    p.add_argument("--source-class", required=True)
    p.set_defaults(func=cmd_shadow_voi)

    p = sub.add_parser("dual-fixture", help="run the exact rational finite spectral dual certificate fixture")
    p.set_defaults(func=cmd_dual_fixture)

    p = sub.add_parser("formal-spec", help="emit the Lean-target theorem specification without claiming a proof")
    p.set_defaults(func=cmd_formal_spec)

    p = sub.add_parser("cells", help="emit exact R0.10-compatible Problem Atlas cells as JSONL")
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
