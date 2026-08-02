"""Command-line probe for Ω-QUATERNION-CRYSTAL-T."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .core import (
    AffineTransform3D,
    Quaternion,
    radians,
    vector_norm,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="omega-quaternion-crystal",
        description=(
            "Apply an OAK-safe quaternion rotation, isotropic scale, and "
            "translation to a 3D vector."
        ),
    )
    parser.add_argument("--axis", nargs=3, type=float, default=(0.0, 0.0, 1.0))
    parser.add_argument("--angle-deg", type=float, default=90.0)
    parser.add_argument("--vector", nargs=3, type=float, default=(1.0, 0.0, 0.0))
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--translation", nargs=3, type=float, default=(0.0, 0.0, 0.0))
    return parser


def run(args: argparse.Namespace) -> dict[str, object]:
    orientation = Quaternion.from_axis_angle(args.axis, radians(args.angle_deg))
    transform = AffineTransform3D.similarity(
        orientation,
        scale=args.scale,
        translation=args.translation,
    )
    rotated = orientation.rotate_vector(args.vector)
    mapped = transform.apply(args.vector)
    return {
        "status": "prototype",
        "oak_boundary": (
            "Quaternion encodes orientation only; stress, strain, constitutive "
            "laws, units, and boundary conditions remain separate objects."
        ),
        "input": {
            "axis": list(args.axis),
            "angle_degrees": args.angle_deg,
            "vector": list(args.vector),
            "scale": args.scale,
            "translation": list(args.translation),
        },
        "quaternion": {
            "w": orientation.w,
            "x": orientation.x,
            "y": orientation.y,
            "z": orientation.z,
            "norm": orientation.norm(),
        },
        "rotation_matrix": [list(row) for row in orientation.to_rotation_matrix()],
        "rotated_vector": list(rotated),
        "affine_vector": list(mapped),
        "invariants": {
            "input_vector_norm": vector_norm(args.vector),
            "rotated_vector_norm": vector_norm(rotated),
            "affine_jacobian": transform.jacobian_determinant(),
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    print(json.dumps(run(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
