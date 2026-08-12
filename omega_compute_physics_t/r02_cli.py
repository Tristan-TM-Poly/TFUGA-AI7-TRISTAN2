"""Command line surface for Ω-COMPUTE-PHYSICS-T∞ R0.2.

Examples
--------
python -m omega_compute_physics_t.r02_cli validate samples.jsonl --target wall_time_s
python -m omega_compute_physics_t.r02_cli diff old.json new.json --target wall_time_s --variable n --start 10 --stop 10000
python -m omega_compute_physics_t.r02_cli drift atlas.json recent.jsonl --target wall_time_s
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .atlas import EmpiricalResourceModel, ResourceSample
from .complexity_diff import compare_models, geometric_sweep, load_model_from_atlas
from .validation import detect_drift, fit_validated_resource_model


def _read_samples(path: str | Path) -> list[ResourceSample]:
    samples: list[ResourceSample] = []
    for line_number, raw in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw.strip():
            continue
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError(f"line {line_number}: expected JSON object")
        samples.append(
            ResourceSample(
                variables=payload["variables"],
                resources=payload["resources"],
                metadata=payload.get("metadata", {}),
            )
        )
    if not samples:
        raise ValueError("input contains no samples")
    return samples


def _model_payload(model: EmpiricalResourceModel) -> dict[str, Any]:
    payload = model.certificate()
    payload["features"] = [
        {
            "kind": feature.kind,
            "variables": list(feature.variables),
            "powers": list(feature.powers),
            "label": feature.label,
        }
        for feature in model.features
    ]
    payload["coefficients"] = list(model.coefficients)
    return payload


def _write(payload: Any, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def _fixed(values: list[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for item in values:
        name, separator, value = item.partition("=")
        if not separator or not name:
            raise ValueError(f"invalid --fixed value: {item!r}; expected name=value")
        result[name] = float(value)
    return result


def cmd_validate(args: argparse.Namespace) -> int:
    samples = _read_samples(args.samples)
    validated = fit_validated_resource_model(
        samples,
        args.target,
        selection_criterion=args.criterion,
        calibration_fraction=args.calibration_fraction,
        alpha=args.alpha,
        k_folds=args.k_folds,
        seed=args.seed,
    )
    payload = {
        "schema": "omega-compute-physics-evidence/v0.2",
        "kind": "validated-resource-model",
        "model": _model_payload(validated.model),
        "validation": validated.report.to_dict(),
    }
    _write(payload, args.output)
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    old = load_model_from_atlas(args.old_atlas, args.target)
    new = load_model_from_atlas(args.new_atlas, args.target)
    points = geometric_sweep(
        args.variable,
        args.start,
        args.stop,
        count=args.count,
        fixed=_fixed(args.fixed),
    )
    anchor = None
    if args.anchor is not None:
        anchor = _fixed(args.fixed)
        anchor[args.variable] = args.anchor
    report = compare_models(
        old,
        new,
        points,
        direction=args.direction,
        relative_tolerance=args.tolerance,
        elasticity_anchor=anchor,
        include_point_deltas=not args.summary_only,
    )
    payload = {
        "schema": "omega-compute-physics-evidence/v0.2",
        "kind": "complexity-diff",
        "report": report.to_dict(include_points=not args.summary_only),
    }
    _write(payload, args.output)
    return 0


def cmd_drift(args: argparse.Namespace) -> int:
    model = load_model_from_atlas(args.atlas, args.target)
    samples = _read_samples(args.samples)
    report = detect_drift(
        model,
        samples,
        args.target,
        relative_error_threshold=args.threshold,
        trigger_fraction=args.trigger_fraction,
    )
    payload = {
        "schema": "omega-compute-physics-evidence/v0.2",
        "kind": "drift-report",
        "report": report.to_dict(),
    }
    _write(payload, args.output)
    return 1 if report.drift_detected and args.fail_on_drift else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-compute-r02",
        description="OAK-safe validation and Complexity Diff for empirical resource atlases.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="select/validate one empirical resource law")
    validate.add_argument("samples")
    validate.add_argument("--target", required=True)
    validate.add_argument(
        "--criterion",
        default="cv_rmse",
        choices=("cv_rmse", "aic_proxy", "bic_proxy", "mdl_proxy"),
    )
    validate.add_argument("--calibration-fraction", type=float, default=0.2)
    validate.add_argument("--alpha", type=float, default=0.1)
    validate.add_argument("--k-folds", type=int, default=5)
    validate.add_argument("--seed", type=int, default=0)
    validate.add_argument("--output")
    validate.set_defaults(func=cmd_validate)

    diff = sub.add_parser("diff", help="compare two serialized atlas resource laws")
    diff.add_argument("old_atlas")
    diff.add_argument("new_atlas")
    diff.add_argument("--target", required=True)
    diff.add_argument("--variable", required=True)
    diff.add_argument("--start", type=float, required=True)
    diff.add_argument("--stop", type=float, required=True)
    diff.add_argument("--count", type=int, default=32)
    diff.add_argument("--fixed", action="append", default=[])
    diff.add_argument("--anchor", type=float)
    diff.add_argument(
        "--direction",
        choices=("lower-is-better", "higher-is-better"),
        default="lower-is-better",
    )
    diff.add_argument("--tolerance", type=float, default=0.02)
    diff.add_argument("--summary-only", action="store_true")
    diff.add_argument("--output")
    diff.set_defaults(func=cmd_diff)

    drift = sub.add_parser("drift", help="check recent samples against one atlas law")
    drift.add_argument("atlas")
    drift.add_argument("samples")
    drift.add_argument("--target", required=True)
    drift.add_argument("--threshold", type=float, default=0.20)
    drift.add_argument("--trigger-fraction", type=float, default=0.30)
    drift.add_argument("--fail-on-drift", action="store_true")
    drift.add_argument("--output")
    drift.set_defaults(func=cmd_drift)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
