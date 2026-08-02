"""Executable demonstration of Ω-LOGEXP-MORPH-T∞."""

from __future__ import annotations

import json
from dataclasses import asdict

from omega_logexp_morph_t import (
    BranchLedger,
    GeneratorGenome,
    MorphSector,
    bch,
    compress_in_basis,
    matrix,
    matrix_exponential,
    matrix_logarithm_near_identity,
    multiply,
    relative_reconstruction_error,
    scale,
)


def main() -> None:
    rotation = matrix([[0.0, 1.0], [-1.0, 0.0]])
    stretch = matrix([[1.0, 0.0], [0.0, -1.0]])

    left = scale(rotation, 0.08)
    right = scale(stretch, 0.03)
    observed = multiply(matrix_exponential(left), matrix_exponential(right))

    exact_local_log = matrix_logarithm_near_identity(observed)
    bch4 = bch(left, right, order=4)
    coefficients, compressed, log_residual = compress_in_basis(
        exact_local_log,
        [
            rotation,
            stretch,
            matrix([[0.0, 1.0], [1.0, 0.0]]),
        ],
    )
    reconstruction = matrix_exponential(compressed)
    reconstruction_residual = relative_reconstruction_error(
        observed,
        reconstruction,
    )

    genome = GeneratorGenome(
        generator_names=("rotation", "deviatoric_stretch", "symmetric_coupling"),
        coefficients=coefficients,
        branch_ledger=BranchLedger(
            branch="real-near-identity",
            continuity_verified=True,
        ),
        logarithm_residual=log_residual,
        reconstruction_residual=reconstruction_residual,
        domain="2x2 demonstration; finite-dimensional real matrices",
    )

    payload = {
        "observed_transformation": observed,
        "sector": asdict(MorphSector.classify(observed)),
        "exact_local_logarithm": exact_local_log,
        "bch_order_4": bch4,
        "bch_reconstruction_residual": relative_reconstruction_error(
            observed,
            matrix_exponential(bch4),
        ),
        "compressed_genome": genome.to_dict(),
        "oak_boundary": (
            "The demonstration proves local numerical reconstruction only. "
            "It does not identify a physical law without calibrated variables, "
            "units, constraints, provenance, and out-of-sample validation."
        ),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
