"""Executable R0.3 demonstration for Ω-LOGEXP-MORPH-T∞²."""

from __future__ import annotations

import json

from omega_logexp_morph_t.advanced import (
    active_factorization,
    build_morph_codex,
    commutator_graph,
    magnus_second_order_piecewise,
    polar_log_2d,
)
from omega_logexp_morph_t.core import matrix


def main() -> None:
    singular_map = matrix(((1, 2, 3), (2, 4, 6)))
    factor = active_factorization(singular_map)
    codex = build_morph_codex(singular_map)

    crystal_slice = matrix(((1.2, -0.3), (0.4, 0.9)))
    polar = polar_log_2d(crystal_slice)

    rotation = matrix(((0, -1), (1, 0)))
    strain = matrix(((1, 0), (0, -1)))
    commutators = commutator_graph(
        {"rotation": rotation, "strain": strain}
    )
    magnus = magnus_second_order_piecewise(
        (rotation, strain),
        step=0.05,
    )

    report = {
        "active_factorization": {
            "rank": factor.active_rank,
            "pivot_rows": factor.pivot_rows,
            "pivot_columns": factor.pivot_columns,
            "reconstruction_error": factor.reconstruction_error,
            "compression_gain_proxy": factor.compression_gain_proxy,
        },
        "codex": codex.to_dict(),
        "polar_log_2d": {
            "rotation_generator": polar.rotation_generator,
            "strain_generator": polar.strain_generator,
            "singular_values": polar.singular_values,
            "reconstruction_error": polar.reconstruction_error,
        },
        "commutator_edges": [
            {
                "left": edge.left,
                "right": edge.right,
                "norm": edge.commutator_norm,
                "normalized_strength": edge.normalized_strength,
            }
            for edge in commutators
        ],
        "magnus_second_order": magnus,
        "oak_status": (
            "R0.3_EXECUTABLE_PROTOTYPE_REPRESENTATION_IS_NOT_PHYSICAL_PROOF"
        ),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
