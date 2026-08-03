"""Deterministic finite benchmark for the executable theory kernel."""

from __future__ import annotations

from itertools import product
from typing import Any

from .blocks import BlockPartition
from .linalg import as_matrix, outer
from .oak import audit_bundle, audit_square, audit_tower
from .projectors import analyze_2d
from .symmetry import default_rank2_tower_2d

FIXTURE_VALUES = (-2.0, -0.5, 0.0, 1.0, 3.0)


def run_benchmark() -> dict[str, Any]:
    maximum_error = 0.0
    bundle_count = 0
    for values in product(FIXTURE_VALUES, repeat=4):
        bundle = analyze_2d(values[:2], values[2:])
        report = audit_bundle(bundle)
        if not report.passed:
            raise AssertionError(report.to_dict())
        maximum_error = max(maximum_error, bundle.residual_norm)
        bundle_count += 1

    square_fixture = as_matrix(((2.0, -1.0, 4.0), (3.0, 0.5, -2.0), (7.0, 1.0, 9.0)))
    square_report = audit_square(square_fixture)
    tower_report = audit_tower(default_rank2_tower_2d())

    partition = BlockPartition.regular(4, 4, (2,), (2,))
    block_fixture = outer((1.0, 2.0, 3.0, 4.0), (-1.0, 0.5, 2.0, -3.0))
    block_audit = partition.audit(block_fixture)

    passed = square_report.passed and tower_report.passed and bool(block_audit["exact"])
    return {
        "status": "CERTIFIED_FINITE_SOFTWARE_FIXTURES_R0_1" if passed else "REJECTED_R0_1",
        "bundle_fixtures": bundle_count,
        "maximum_reconstruction_error": maximum_error,
        "square_audit": square_report.to_dict(),
        "tower_audit": tower_report.to_dict(),
        "block_audit": block_audit,
        "claims": {
            "general_theorem_proved_by_benchmark": False,
            "all_tensor_factorizations_implemented": False,
            "new_physics_validated": False,
            "finite_software_fixtures_certified": passed,
        },
    }
