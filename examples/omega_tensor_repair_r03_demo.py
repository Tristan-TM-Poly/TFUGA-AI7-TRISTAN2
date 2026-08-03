"""Executable R0.3 demonstration for Ω-TENSOR-REPAIR-T."""

from __future__ import annotations

import json

from omega_tensor_repair_t import (
    ContractionPlan,
    ContractionStep,
    DenseTensor,
    analyze_square_irreducible,
    basis_orthonormality_error,
    square_irreducible_basis,
    young_dimension_atlas,
)
from omega_tensor_repair_t.linalg import as_matrix


def main() -> None:
    matrix = as_matrix(
        (
            (2.0, -1.0, 3.0),
            (4.0, 5.0, 0.5),
            (-2.0, 1.5, 7.0),
        )
    )
    analysis = analyze_square_irreducible(matrix)

    rank4 = DenseTensor(
        (2, 2, 2, 2),
        tuple(float(index + 1) for index in range(16)),
    )
    contraction = ContractionPlan(
        (
            ContractionStep(0, 1, "trace-first-pair"),
            ContractionStep(0, 1, "trace-second-pair"),
        ),
        name="double-trace-demo",
    ).apply(rank4)

    basis = square_irreducible_basis(3)
    payload = {
        "basis": {
            "size": 3,
            "cardinality": len(basis),
            "orthonormality_error": basis_orthonormality_error(basis),
            "sectors": [element.sector for element in basis],
        },
        "analysis": analysis.to_dict(),
        "double_trace": contraction.to_dict(),
        "young_order_4_dimension_3": young_dimension_atlas(4, 3),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
