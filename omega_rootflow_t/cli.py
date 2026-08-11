"""CLI for Ω-ROOTFLOW-T∞."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import numpy as np

from .continuation import continue_roots
from .core import root_conditions, root_jacobian, roots
from .oak import audit_rootflow


def _parse_coefficients(text: str) -> np.ndarray:
    try:
        values = [complex(part.strip()) for part in text.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid complex coefficient: {exc}") from exc
    if len(values) < 2:
        raise argparse.ArgumentTypeError("provide at least two comma-separated coefficients")
    return np.asarray(values, dtype=np.complex128)


def _complex(value: complex) -> dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag)}


def _complex_vector(values: np.ndarray) -> list[dict[str, float]]:
    return [_complex(complex(value)) for value in values]


def analyze_payload(coefficients: np.ndarray) -> dict[str, object]:
    rr = roots(coefficients)
    jac = root_jacobian(coefficients, rr)
    conditions = root_conditions(coefficients, rr)
    audit = audit_rootflow(coefficients)
    return {
        "system": "Ω-ROOTFLOW-T∞",
        "version": "R0.1",
        "coefficient_order": "ascending [a0,...,an]",
        "degree": int(coefficients.size - 1),
        "roots": _complex_vector(rr),
        "conditions": [
            {
                "root": _complex(item.root),
                "derivative_magnitude": item.derivative_magnitude,
                "reciprocal_derivative": item.reciprocal_derivative,
                "residual": item.residual,
                "near_singular": item.near_singular,
            }
            for item in conditions
        ],
        "root_jacobian": [[_complex(complex(value)) for value in row] for row in jac],
        "audit": audit.to_dict(),
        "claims": {
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
            "scope": "analytic simple-root identities plus numerical software checks",
        },
    }


def continuation_payload(start: np.ndarray, end: np.ndarray, steps: int) -> dict[str, object]:
    result = continue_roots(start, end, steps=steps)
    return {
        "system": "Ω-ROOTFLOW-T∞",
        "version": "R0.1",
        "steps": [
            {
                "t": item.parameter,
                "roots": _complex_vector(item.roots),
                "predictor_residual": item.predictor_residual,
                "corrected_residual": item.corrected_residual,
                "minimum_derivative": item.minimum_derivative,
            }
            for item in result.steps
        ],
    }


def _write(payload: dict[str, object], output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ω-ROOTFLOW-T∞ differential polynomial-root engine")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="roots, analytic Jacobian, conditioning, OAK checks")
    analyze.add_argument("--coeffs", required=True, type=_parse_coefficients, help="ascending a0,a1,...,an")
    analyze.add_argument("--output")
    cont = sub.add_parser("continue", help="track roots between two coefficient vectors")
    cont.add_argument("--start", required=True, type=_parse_coefficients)
    cont.add_argument("--end", required=True, type=_parse_coefficients)
    cont.add_argument("--steps", type=int, default=32)
    cont.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        _write(analyze_payload(args.coeffs), args.output)
        return 0
    if args.command == "continue":
        _write(continuation_payload(args.start, args.end, args.steps), args.output)
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
