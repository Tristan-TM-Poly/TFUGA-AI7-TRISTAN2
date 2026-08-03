"""Deterministic OAK benchmark for Ω-TENSOR-REPAIR-T R0.3."""

from __future__ import annotations

import hashlib
import json
from math import factorial
from typing import Any

from .contractions import ContractionPlan, ContractionStep
from .higher_order import DenseTensor
from .irreducible_basis import analyze_square_irreducible, basis_orthonormality_error, square_irreducible_basis
from .linalg import as_matrix
from .young import partitions, young_dimension_atlas


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_benchmark_r03() -> dict[str, Any]:
    basis_cases = 0
    maximum_orthonormality_error = 0.0
    maximum_reconstruction_error = 0.0
    sector_dimensions: dict[str, dict[str, int]] = {}

    for size in range(1, 9):
        basis = square_irreducible_basis(size)
        maximum_orthonormality_error = max(
            maximum_orthonormality_error,
            basis_orthonormality_error(basis),
        )
        matrix = as_matrix(
            ((row + 1) * 0.75 - (col + 1) * 1.25 + ((row + 2 * col) % 5) for col in range(size))
            for row in range(size)
        )
        analysis = analyze_square_irreducible(matrix)
        maximum_reconstruction_error = max(maximum_reconstruction_error, analysis.reconstruction_error)
        sector_dimensions[str(size)] = {
            "symmetric_traceless": len(analysis.symmetric_traceless),
            "isotropic": len(analysis.isotropic),
            "antisymmetric": len(analysis.antisymmetric),
            "total": len(analysis.full_coordinates),
        }
        basis_cases += 1

    partition_cases = 0
    hook_identity_pass = True
    schur_nonnegative = True
    atlas_digest_input: list[dict[str, object]] = []
    for order in range(1, 8):
        diagrams = partitions(order)
        hook_identity_pass = hook_identity_pass and (
            sum(diagram.standard_tableau_count() ** 2 for diagram in diagrams) == factorial(order)
        )
        for ambient_dimension in range(1, 8):
            atlas = young_dimension_atlas(order, ambient_dimension)
            schur_nonnegative = schur_nonnegative and all(entry["schur_dimension"] >= 0 for entry in atlas)
            atlas_digest_input.extend(atlas)
            partition_cases += len(atlas)

    tensor = DenseTensor((3, 3, 3, 3), tuple(float((index * 11) % 17 - 8) for index in range(81)))
    contraction = ContractionPlan(
        (
            ContractionStep(0, 1, "trace-01"),
            ContractionStep(0, 1, "trace-23"),
        ),
        name="rank4-double-trace",
    ).apply(tensor)

    invariants = {
        "basis_cardinality": all(values["total"] == size * size for size, values in ((int(key), value) for key, value in sector_dimensions.items())),
        "basis_orthonormal": maximum_orthonormality_error <= 1e-12,
        "basis_reconstructs": maximum_reconstruction_error <= 1e-10,
        "hook_length_identity": hook_identity_pass,
        "schur_dimensions_nonnegative": schur_nonnegative,
        "contraction_reaches_scalar": contraction.output.rank == 0,
        "contraction_receipts_complete": len(contraction.receipts) == 2,
    }

    payload: dict[str, Any] = {
        "status": "CERTIFIED_EXTENDED_SOFTWARE_FIXTURES_R0_3" if all(invariants.values()) else "FAILED_R0_3",
        "basis_cases": basis_cases,
        "partition_atlas_entries": partition_cases,
        "maximum_orthonormality_error": maximum_orthonormality_error,
        "maximum_reconstruction_error": maximum_reconstruction_error,
        "sector_dimensions": sector_dimensions,
        "double_trace": contraction.output.scalar,
        "contraction_receipts": [receipt.to_dict() for receipt in contraction.receipts],
        "young_atlas_sha256": hashlib.sha256(
            json.dumps(atlas_digest_input, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "invariants": invariants,
        "claims": {
            "mixed_young_operator_is_orthogonal_projector": False,
            "benchmark_is_general_proof": False,
            "all_tensor_networks_are_supported": False,
            "new_physics_validated": False,
        },
    }
    payload["receipt_sha256"] = _stable_hash(payload)
    return payload
