"""Standalone CLI for R11 principal-minor and xi-derivative constraints."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from fractions import Fraction

from .principal_constraints import all_principal_minor_constraints
from .symbolic_hankel import tensor_lift_constraint
from .xi_constraints import xi_derivative_constraint


def _jsonable(value):
    if isinstance(value, Fraction):
        return {
            "exact": str(value),
            "numerator": value.numerator,
            "denominator": value.denominator,
        }
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-zeta-square-r11",
        description="Compile exact finite R10 PSD obligations; never proves RH.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    tensor = sub.add_parser("tensor", help="full Hankel determinant in TensorProdLift monomials")
    tensor.add_argument("--size", type=int, required=True)
    tensor.add_argument("--shift", type=int, default=0)

    principal = sub.add_parser("principal", help="all principal-minor constraints of H_N^(shift)")
    principal.add_argument("--size", type=int, required=True)
    principal.add_argument("--shift", type=int, default=0)

    xi = sub.add_parser("xi", help="full determinant as integer polynomial in xi central derivatives")
    xi.add_argument("--size", type=int, required=True)
    xi.add_argument("--shift", type=int, default=0)

    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "tensor":
        payload = {
            "schema": "omega-zeta-square-r11-tensor/1",
            "constraint": tensor_lift_constraint(args.size, args.shift),
            "proves_rh": False,
        }
    elif args.command == "principal":
        constraints = all_principal_minor_constraints(args.size, args.shift)
        payload = {
            "schema": "omega-zeta-square-r11-principal/1",
            "full_size": args.size,
            "shift": args.shift,
            "constraint_count": len(constraints),
            "constraints": constraints,
            "oak": {
                "finite_psd_requires_all_principal_minors": True,
                "all_orders_r10_still_required": True,
            },
            "proves_rh": False,
        }
    else:
        payload = {
            "schema": "omega-zeta-square-r11-xi/1",
            "constraint": xi_derivative_constraint(args.size, args.shift),
            "oak": {
                "d0_positive_required_for_sign_equivalence": True,
                "all_orders_r10_still_required": True,
            },
            "proves_rh": False,
        }
    print(json.dumps(_jsonable(payload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
