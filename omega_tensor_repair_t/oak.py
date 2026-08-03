"""OAK verification for exactness, dimensions and epistemic boundaries."""

from __future__ import annotations

from .linalg import Matrix, frobenius_norm, subtract
from .models import AuditCheck, OAKReport, RepairBundle, SymmetryTower
from .projectors import decompose_square, dimension_identity, reconstruct_square
from .symmetry import validate_tower

BOUNDARIES = (
    "The classical tensor product keeps dimension dim(V)·dim(W).",
    "Derived channels are projections or redundant views, not automatically independent degrees of freedom.",
    "Finite numerical checks certify only the tested implementation and fixtures.",
    "No new physical law, universal optimality or experimental validation is claimed.",
    "Approximate compression must retain an explicit residual and domain of validity.",
)


def audit_bundle(bundle: RepairBundle, *, tolerance: float = 1e-10) -> OAKReport:
    expected_dimension = len(bundle.input_left) * len(bundle.input_right)
    reconstructed_error = frobenius_norm(subtract(bundle.full_tensor, bundle.reconstruction))
    channel_names = {channel.name for channel in bundle.channels}
    checks = (
        AuditCheck(
            "classical-dimension",
            bundle.full_dimension == expected_dimension,
            bundle.full_dimension,
            expected_dimension,
        ),
        AuditCheck(
            "exact-reconstruction",
            reconstructed_error <= tolerance,
            reconstructed_error,
            0.0,
            tolerance,
        ),
        AuditCheck(
            "required-2d-channels",
            {"full", "symmetric", "symmetric_traceless", "trace", "antisymmetric"}.issubset(channel_names),
            str(sorted(channel_names)),
            "full,symmetric,symmetric_traceless,trace,antisymmetric",
        ),
        AuditCheck(
            "epistemic-boundary",
            bundle.claims.get("new_physical_law_claimed") is False,
            bundle.claims.get("new_physical_law_claimed", "missing"),
            False,
        ),
    )
    status = "CERTIFIED_EXACT_FIXTURE_R0_1" if all(check.passed for check in checks) else "REJECTED_R0_1"
    return OAKReport(
        status=status,
        checks=checks,
        metrics={
            "input_left_dimension": len(bundle.input_left),
            "input_right_dimension": len(bundle.input_right),
            "full_dimension": bundle.full_dimension,
            "channel_count": len(bundle.channels),
            "reconstruction_error": reconstructed_error,
        },
        boundaries=BOUNDARIES,
    )


def audit_square(matrix: Matrix, *, tolerance: float = 1e-10) -> OAKReport:
    parts = decompose_square(matrix)
    reconstruction = reconstruct_square(parts)
    error = frobenius_norm(subtract(matrix, reconstruction))
    size = len(matrix)
    dims = dimension_identity(size)
    dimension_sum = dims["symmetric_traceless"] + dims["antisymmetric"] + dims["trace"]
    checks = (
        AuditCheck("square-reconstruction", error <= tolerance, error, 0.0, tolerance),
        AuditCheck("dimension-partition", dimension_sum == dims["full"], dimension_sum, dims["full"]),
    )
    return OAKReport(
        status="CERTIFIED_SQUARE_DECOMPOSITION_R0_1" if all(check.passed for check in checks) else "REJECTED_R0_1",
        checks=checks,
        metrics={**dims, "reconstruction_error": error},
        boundaries=BOUNDARIES,
    )


def audit_tower(tower: SymmetryTower) -> OAKReport:
    validation = validate_tower(tower)
    check = AuditCheck(
        "tower-dimension-conservation",
        bool(validation["valid"]),
        str(validation["errors"]),
        "[]",
    )
    return OAKReport(
        status="CERTIFIED_TOWER_R0_1" if check.passed else "REJECTED_R0_1",
        checks=(check,),
        metrics={"node_count": int(validation["node_count"]), "root_count": int(validation["root_count"])},
        boundaries=BOUNDARIES,
    )
