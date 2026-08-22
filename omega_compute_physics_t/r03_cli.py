"""CLI for Ω-COMPUTE-PHYSICS-T∞ R0.3 active and inverse design."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .active import geometric_design_space, select_next_experiments
from .atlas import ResourceSample
from .budget import ResourceConstraint, compile_budget, pareto_front
from .complexity_diff import load_model_from_atlas


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def _read_samples(path: str | Path) -> list[ResourceSample]:
    samples: list[ResourceSample] = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        payload = json.loads(raw)
        samples.append(
            ResourceSample(
                variables=payload["variables"],
                resources=payload["resources"],
                metadata=payload.get("metadata", {}),
            )
        )
    return samples


def _bounds(values: list[str]) -> dict[str, tuple[float, float]]:
    result: dict[str, tuple[float, float]] = {}
    for item in values:
        name, sep, interval = item.partition("=")
        low, colon, high = interval.partition(":")
        if not sep or not colon or not name:
            raise ValueError(f"invalid bound {item!r}; expected name=low:high")
        result[name] = (float(low), float(high))
    if not result:
        raise ValueError("at least one --bound is required")
    return result


def _models(values: list[str]) -> dict[str, Any]:
    result = {}
    for item in values:
        target, sep, path = item.partition("=")
        if not sep or not target or not path:
            raise ValueError(f"invalid model {item!r}; expected target=atlas.json")
        result[target] = load_model_from_atlas(path, target)
    if not result:
        raise ValueError("at least one --model is required")
    return result


def _constraint(item: str) -> ResourceConstraint:
    if "<=" in item:
        target, value = item.split("<=", 1)
        return ResourceConstraint(target.strip(), upper=float(value))
    if ">=" in item:
        target, value = item.split(">=", 1)
        return ResourceConstraint(target.strip(), lower=float(value))
    raise ValueError(f"invalid constraint {item!r}; expected target<=value or target>=value")


def _uncertainty(values: list[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for item in values:
        target, sep, value = item.partition("=")
        if not sep:
            raise ValueError(f"invalid uncertainty {item!r}; expected target=radius")
        result[target] = float(value)
    return result


def _objective(item: str) -> tuple[str, str]:
    target, sep, direction = item.partition(":")
    if not sep or direction not in {"minimize", "maximize"}:
        raise ValueError(f"invalid objective {item!r}; expected target:minimize|maximize")
    return target, direction


def cmd_active(args: argparse.Namespace) -> int:
    models = [load_model_from_atlas(path, args.target) for path in args.atlas]
    cost_model = None
    if args.cost_model:
        cost_target, sep, cost_path = args.cost_model.partition("=")
        if not sep:
            raise ValueError("--cost-model expects target=atlas.json")
        cost_model = load_model_from_atlas(cost_path, cost_target)
    candidates = geometric_design_space(
        _bounds(args.bound),
        levels=args.levels,
        max_points=args.max_points,
    )
    existing = _read_samples(args.existing_samples) if args.existing_samples else []
    selected = select_next_experiments(
        models,
        candidates,
        existing_samples=existing,
        cost_model=cost_model,
        count=args.count,
        min_log_distance=args.min_log_distance,
        disagreement_weight=args.disagreement_weight,
        novelty_weight=args.novelty_weight,
        cost_power=args.cost_power,
    )
    _write(
        {
            "schema": "omega-compute-physics-evidence/v0.3",
            "kind": "active-benchmark-plan",
            "target": args.target,
            "candidate_count": len(candidates),
            "selected": [item.to_dict() for item in selected],
            "oak_warning": (
                "Selection uses a bounded information proxy and is not an exact "
                "global expected-information-gain optimum."
            ),
        },
        args.output,
    )
    return 0


def cmd_budget(args: argparse.Namespace) -> int:
    models = _models(args.model)
    candidates = geometric_design_space(
        _bounds(args.bound),
        levels=args.levels,
        max_points=args.max_points,
    )
    constraints = tuple(_constraint(item) for item in args.constraint)
    objective_target = None
    objective_direction = "minimize"
    if args.objective:
        objective_target, objective_direction = _objective(args.objective)
    report = compile_budget(
        models,
        candidates,
        constraints=constraints,
        uncertainty_radii=_uncertainty(args.uncertainty),
        objective_target=objective_target,
        objective_direction=objective_direction,
    )
    _write(
        {
            "schema": "omega-compute-physics-evidence/v0.3",
            "kind": "budget-compile",
            "report": report.to_dict(include_evaluations=not args.summary_only),
        },
        args.output,
    )
    return 2 if report.best is None and args.fail_if_infeasible else 0


def cmd_pareto(args: argparse.Namespace) -> int:
    models = _models(args.model)
    candidates = geometric_design_space(
        _bounds(args.bound),
        levels=args.levels,
        max_points=args.max_points,
    )
    objectives = dict(_objective(item) for item in args.objective)
    front = pareto_front(
        models,
        candidates,
        objectives=objectives,
        constraints=tuple(_constraint(item) for item in args.constraint),
        uncertainty_radii=_uncertainty(args.uncertainty),
    )
    _write(
        {
            "schema": "omega-compute-physics-evidence/v0.3",
            "kind": "pareto-front",
            "objectives": objectives,
            "candidate_count": len(candidates),
            "front": [item.to_dict() for item in front],
            "oak_warning": (
                "This is a nondominated set only over the supplied bounded "
                "candidate design space and empirical models."
            ),
        },
        args.output,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="omega-compute-r03")
    sub = parser.add_subparsers(dest="command", required=True)

    active = sub.add_parser("active")
    active.add_argument("--atlas", action="append", required=True)
    active.add_argument("--target", required=True)
    active.add_argument("--bound", action="append", required=True)
    active.add_argument("--levels", type=int, default=5)
    active.add_argument("--max-points", type=int, default=4096)
    active.add_argument("--count", type=int, default=1)
    active.add_argument("--existing-samples")
    active.add_argument("--cost-model")
    active.add_argument("--min-log-distance", type=float, default=0.0)
    active.add_argument("--disagreement-weight", type=float, default=1.0)
    active.add_argument("--novelty-weight", type=float, default=0.5)
    active.add_argument("--cost-power", type=float, default=1.0)
    active.add_argument("--output")
    active.set_defaults(func=cmd_active)

    budget = sub.add_parser("budget")
    budget.add_argument("--model", action="append", required=True)
    budget.add_argument("--bound", action="append", required=True)
    budget.add_argument("--constraint", action="append", default=[])
    budget.add_argument("--uncertainty", action="append", default=[])
    budget.add_argument("--objective")
    budget.add_argument("--levels", type=int, default=5)
    budget.add_argument("--max-points", type=int, default=4096)
    budget.add_argument("--summary-only", action="store_true")
    budget.add_argument("--fail-if-infeasible", action="store_true")
    budget.add_argument("--output")
    budget.set_defaults(func=cmd_budget)

    pareto = sub.add_parser("pareto")
    pareto.add_argument("--model", action="append", required=True)
    pareto.add_argument("--bound", action="append", required=True)
    pareto.add_argument("--constraint", action="append", default=[])
    pareto.add_argument("--uncertainty", action="append", default=[])
    pareto.add_argument("--objective", action="append", required=True)
    pareto.add_argument("--levels", type=int, default=5)
    pareto.add_argument("--max-points", type=int, default=4096)
    pareto.add_argument("--output")
    pareto.set_defaults(func=cmd_pareto)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
