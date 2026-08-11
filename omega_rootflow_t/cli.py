"""CLI for Ω-ROOTFLOW-T∞."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

import numpy as np

from .adaptive import continue_roots_adaptive
from .basis import conditioning_atlas
from .continuation import continue_roots
from .core import root_conditions, root_jacobian, roots
from .monodromy import quadratic_square_root_loop, track_coefficient_path
from .oak import audit_rootflow
from .projective import projective_roots
from .spectral import audit_spectral_geometry, inverse_design_roots

VERSION = "R0.3"


def _parse_complex_vector(text: str, *, minimum: int = 1) -> np.ndarray:
    try:
        values = [complex(part.strip()) for part in text.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid complex value: {exc}") from exc
    if len(values) < minimum:
        raise argparse.ArgumentTypeError(
            f"provide at least {minimum} comma-separated value{'s' if minimum != 1 else ''}"
        )
    return np.asarray(values, dtype=np.complex128)


def _parse_coefficients(text: str) -> np.ndarray:
    return _parse_complex_vector(text, minimum=2)


def _parse_roots(text: str) -> np.ndarray:
    return _parse_complex_vector(text, minimum=1)


def _complex(value: complex) -> dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag)}


def _complex_vector(values: np.ndarray) -> list[dict[str, float]]:
    return [_complex(complex(value)) for value in values]


def analyze_payload(coefficients: np.ndarray) -> dict[str, object]:
    rr = roots(coefficients)
    jac = root_jacobian(coefficients, rr)
    conditions = root_conditions(coefficients, rr)
    audit = audit_rootflow(coefficients)
    spectral = audit_spectral_geometry(coefficients)
    return {
        "system": "Ω-ROOTFLOW-T∞",
        "version": VERSION,
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
        "spectral_audit": spectral.to_dict(),
        "claims": {
            "theorem_claimed": False,
            "scientific_validation_claimed": False,
            "scope": "analytic simple-root identities plus numerical software cross-checks",
        },
    }


def continuation_payload(start: np.ndarray, end: np.ndarray, steps: int) -> dict[str, object]:
    result = continue_roots(start, end, steps=steps)
    return {
        "system": "Ω-ROOTFLOW-T∞",
        "version": VERSION,
        "mode": "fixed-step",
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


def adaptive_continuation_payload(
    start: np.ndarray,
    end: np.ndarray,
    *,
    initial_step: float,
    minimum_step: float,
    maximum_step: float,
    predictor_tolerance: float,
) -> dict[str, object]:
    result = continue_roots_adaptive(
        start,
        end,
        initial_step=initial_step,
        minimum_step=minimum_step,
        maximum_step=maximum_step,
        predictor_tolerance=predictor_tolerance,
    )
    return {
        "system": "Ω-ROOTFLOW-T∞",
        "version": VERSION,
        "mode": "adaptive",
        "status": result.status,
        "rejected_attempts": result.rejected_attempts,
        "minimum_step_size": result.minimum_step_size,
        "steps": [
            {
                "t": item.parameter,
                "step_size": item.step_size,
                "attempts": item.attempts,
                "roots": _complex_vector(item.roots),
                "predictor_residual": item.predictor_residual,
                "corrected_residual": item.corrected_residual,
                "minimum_derivative": item.minimum_derivative,
            }
            for item in result.steps
        ],
        "claims": {
            "theorem_claimed": result.theorem_claimed,
            "scientific_validation_claimed": result.scientific_validation_claimed,
        },
    }


def spectral_payload(coefficients: np.ndarray) -> dict[str, object]:
    audit = audit_spectral_geometry(coefficients)
    return {
        "system": "Ω-ROOTFLOW-T∞",
        "version": VERSION,
        "mode": "spectral-crosscheck",
        "audit": audit.to_dict(),
    }


def basis_atlas_payload(coefficients: np.ndarray) -> dict[str, object]:
    atlas = conditioning_atlas(coefficients)
    return {
        "system": "Ω-ROOTFLOW-T∞",
        "version": VERSION,
        "mode": "basis-conditioning-atlas",
        "atlas": atlas.to_dict(),
    }


def projective_payload(coefficients: np.ndarray) -> dict[str, object]:
    spectrum = projective_roots(coefficients)
    return {
        "system": "Ω-ROOTFLOW-T∞",
        "version": VERSION,
        "mode": "projective-spectrum",
        "spectrum": spectrum.to_dict(),
    }


def monodromy_demo_payload(samples: int, subdivisions: int) -> dict[str, object]:
    path = quadratic_square_root_loop(samples)
    result = track_coefficient_path(path, subdivisions=subdivisions)
    return {
        "system": "Ω-ROOTFLOW-T∞",
        "version": VERSION,
        "mode": "monodromy-demo-z2-minus-t",
        "result": result.to_dict(),
    }


def inverse_design_payload(
    coefficients: np.ndarray,
    target_roots: np.ndarray,
    *,
    real_coefficients: bool,
    max_iterations: int,
    tolerance: float,
) -> dict[str, object]:
    result = inverse_design_roots(
        coefficients,
        target_roots,
        real_coefficients=real_coefficients,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    return {
        "system": "Ω-ROOTFLOW-T∞",
        "version": VERSION,
        "mode": "inverse-design",
        "status": result.status,
        "converged": result.converged,
        "root_error_norm": result.root_error_norm,
        "coefficients": _complex_vector(result.coefficients),
        "roots": _complex_vector(result.roots),
        "target_roots": _complex_vector(result.target_roots),
        "iterations": [
            {
                "iteration": item.iteration,
                "root_error_norm": item.root_error_norm,
                "update_norm": item.update_norm,
                "accepted_scale": item.accepted_scale,
                "linear_rank": item.linear_rank,
                "linear_condition_number": item.linear_condition_number,
                "max_root_residual": item.max_root_residual,
            }
            for item in result.steps
        ],
        "claims": {
            "theorem_claimed": result.theorem_claimed,
            "scientific_validation_claimed": result.scientific_validation_claimed,
        },
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

    spectral = sub.add_parser("spectral", help="companion-matrix and discriminant geometry cross-check")
    spectral.add_argument("--coeffs", required=True, type=_parse_coefficients)
    spectral.add_argument("--output")

    basis = sub.add_parser("basis-atlas", help="compare monomial/Chebyshev/Legendre/Bernstein conditioning")
    basis.add_argument("--coeffs", required=True, type=_parse_coefficients)
    basis.add_argument("--output")

    projective = sub.add_parser("projective", help="represent the nominal root divisor including infinity")
    projective.add_argument("--coeffs", required=True, type=_parse_coefficients)
    projective.add_argument("--output")

    monodromy = sub.add_parser("monodromy-demo", help="track z^2-t roots around one loop enclosing t=0")
    monodromy.add_argument("--samples", type=int, default=17)
    monodromy.add_argument("--subdivisions", type=int, default=2)
    monodromy.add_argument("--output")

    cont = sub.add_parser("continue", help="track roots between two coefficient vectors")
    cont.add_argument("--start", required=True, type=_parse_coefficients)
    cont.add_argument("--end", required=True, type=_parse_coefficients)
    cont.add_argument("--steps", type=int, default=32)
    cont.add_argument("--output")

    adaptive = sub.add_parser("adaptive", help="condition-aware adaptive root continuation")
    adaptive.add_argument("--start", required=True, type=_parse_coefficients)
    adaptive.add_argument("--end", required=True, type=_parse_coefficients)
    adaptive.add_argument("--initial-step", type=float, default=0.125)
    adaptive.add_argument("--minimum-step", type=float, default=1e-5)
    adaptive.add_argument("--maximum-step", type=float, default=0.25)
    adaptive.add_argument("--predictor-tolerance", type=float, default=1e-3)
    adaptive.add_argument("--output")

    inverse = sub.add_parser("inverse-design", help="iteratively fit coefficients to a target root spectrum")
    inverse.add_argument("--coeffs", required=True, type=_parse_coefficients)
    inverse.add_argument("--target-roots", required=True, type=_parse_roots)
    inverse.add_argument("--complex-coefficients", action="store_false", dest="real_coefficients")
    inverse.set_defaults(real_coefficients=True)
    inverse.add_argument("--max-iterations", type=int, default=24)
    inverse.add_argument("--tolerance", type=float, default=1e-10)
    inverse.add_argument("--output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        _write(analyze_payload(args.coeffs), args.output)
        return 0
    if args.command == "spectral":
        _write(spectral_payload(args.coeffs), args.output)
        return 0
    if args.command == "basis-atlas":
        _write(basis_atlas_payload(args.coeffs), args.output)
        return 0
    if args.command == "projective":
        _write(projective_payload(args.coeffs), args.output)
        return 0
    if args.command == "monodromy-demo":
        _write(monodromy_demo_payload(args.samples, args.subdivisions), args.output)
        return 0
    if args.command == "continue":
        _write(continuation_payload(args.start, args.end, args.steps), args.output)
        return 0
    if args.command == "adaptive":
        _write(
            adaptive_continuation_payload(
                args.start,
                args.end,
                initial_step=args.initial_step,
                minimum_step=args.minimum_step,
                maximum_step=args.maximum_step,
                predictor_tolerance=args.predictor_tolerance,
            ),
            args.output,
        )
        return 0
    if args.command == "inverse-design":
        _write(
            inverse_design_payload(
                args.coeffs,
                args.target_roots,
                real_coefficients=args.real_coefficients,
                max_iterations=args.max_iterations,
                tolerance=args.tolerance,
            ),
            args.output,
        )
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
