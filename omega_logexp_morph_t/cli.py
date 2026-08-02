"""Command-line interface for Ω-LOGEXP-MORPH-T∞."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Sequence

from .core import (
    MorphSector,
    matrix,
    matrix_exponential,
    matrix_logarithm_near_identity,
    relative_reconstruction_error,
)


def _json_matrix(raw: str):
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError(f"Invalid JSON matrix: {error}") from error
    try:
        return matrix(payload)
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-logexp-morph",
        description=(
            "Compute a finite-dimensional matrix exponential or a guarded "
            "near-identity real logarithm."
        ),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--generator",
        type=_json_matrix,
        help='Generator matrix as JSON, for example "[[0,0.1],[-0.1,0]]".',
    )
    mode.add_argument(
        "--transformation",
        type=_json_matrix,
        help="Near-identity transformation matrix as JSON.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.generator is not None:
        generator = args.generator
        transformation = matrix_exponential(generator)
        payload = {
            "mode": "exp",
            "generator": generator,
            "transformation": transformation,
            "sector": asdict(MorphSector.classify(transformation)),
        }
    else:
        transformation = args.transformation
        generator = matrix_logarithm_near_identity(transformation)
        reconstruction = matrix_exponential(generator)
        payload = {
            "mode": "log",
            "transformation": transformation,
            "generator": generator,
            "reconstruction": reconstruction,
            "reconstruction_residual": relative_reconstruction_error(
                transformation,
                reconstruction,
            ),
            "sector": asdict(MorphSector.classify(transformation)),
        }

    print(json.dumps(payload, indent=args.indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
