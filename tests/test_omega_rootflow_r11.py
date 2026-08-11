import json
from fractions import Fraction

from omega_rootflow_t import (
    ExactRootCluster,
    exact_affine_solve,
    exact_fixed_hermite_matrix,
    exact_hermite_design,
    exact_mobile_cluster_matrix,
    exact_multi_cluster_tangent,
    exact_nullspace,
    exact_rank,
)
from omega_rootflow_t.cli import main


COEFFS = (-4, 8, -1, -5, 1, 1)
CLUSTERS = (ExactRootCluster(Fraction(1), 3), ExactRootCluster(Fraction(-2), 2))


def test_exact_mobile_matrix_and_rank_match_closed_form() -> None:
    matrix = exact_mobile_cluster_matrix(CLUSTERS, tuple(range(6)))
    assert matrix == (
        (1, 1, 1, 1, 1, 1),
        (0, 1, 2, 3, 4, 5),
        (1, -2, 4, -8, 16, -32),
    )
    assert exact_rank(matrix) == 3
    basis = exact_nullspace(matrix)
    assert len(basis) == 3
    for row in matrix:
        for vector in basis:
            assert sum(left * right for left, right in zip(row, vector, strict=True)) == 0


def test_exact_multicluster_tangent_has_exact_zero_residual() -> None:
    result = exact_multi_cluster_tangent(COEFFS, CLUSTERS, tuple(range(6)))
    assert result.status == "OAK_PASS_EXACT_MULTICLUSTER_TANGENT"
    assert result.constraint_rank == 3
    assert result.expected_full_space_codimension == 3
    assert len(result.tangent_basis) == 3
    assert len(result.cluster_velocities) == 3
    assert all(len(item) == 2 for item in result.cluster_velocities)
    assert result.exact_constraint_residual_zero
    assert result.theorem_claimed is False


def test_exact_fixed_hermite_square_matrix_has_determinant_1458() -> None:
    matrix = exact_fixed_hermite_matrix(CLUSTERS, tuple(range(5)))
    assert len(matrix) == 5
    assert exact_rank(matrix) == 5
    design = exact_hermite_design((0, 0, 0, 0, 0, 1), CLUSTERS, free_degrees=range(5))
    assert design.square_constraint_determinant == 1458


def test_exact_hermite_design_recovers_partition_3_2_polynomial() -> None:
    design = exact_hermite_design((0, 0, 0, 0, 0, 1), CLUSTERS, free_degrees=range(5))
    assert design.status == "OAK_PASS_EXACT_HERMITE_DESIGN"
    assert design.constraint_rank == 5
    assert design.coefficients == tuple(Fraction(value) for value in COEFFS)
    assert design.coefficient_update == (-4, 8, -1, -5, 1, 0)
    assert design.exact_residual_zero


def test_exact_fractional_cluster_design_is_rational() -> None:
    # (z-1/2)^2 (z+1/3)
    clusters = (
        ExactRootCluster(Fraction(1, 2), 2),
        ExactRootCluster(Fraction(-1, 3), 1),
    )
    design = exact_hermite_design((0, 0, 0, 1), clusters, free_degrees=(0, 1, 2))
    assert design.status == "OAK_PASS_EXACT_HERMITE_DESIGN"
    assert design.coefficients == (Fraction(1, 12), Fraction(-1, 12), Fraction(-2, 3), Fraction(1))
    assert design.exact_residual_zero


def test_exact_affine_solver_is_deterministic_for_underdetermined_system() -> None:
    matrix = ((Fraction(1), Fraction(1), Fraction(0)),)
    target = (Fraction(3),)
    solution = exact_affine_solve(matrix, target)
    assert solution == (3, 0, 0)


def test_r11_cli_exact_multicluster_and_design(tmp_path) -> None:
    tangent_path = tmp_path / "tangent.json"
    design_path = tmp_path / "design.json"
    assert main([
        "exact-multi-cluster-tangent",
        "--coeffs=-4,8,-1,-5,1,1",
        "--clusters", "1:3,-2:2",
        "--degrees", "0,1,2,3,4,5",
        "--output", str(tangent_path),
    ]) == 0
    assert main([
        "exact-hermite-design",
        "--coeffs=0,0,0,0,0,1",
        "--clusters", "1:3,-2:2",
        "--free-degrees", "0,1,2,3,4",
        "--output", str(design_path),
    ]) == 0
    tangent = json.loads(tangent_path.read_text(encoding="utf-8"))
    design = json.loads(design_path.read_text(encoding="utf-8"))
    assert tangent["version"] == "R0.11"
    assert tangent["tangent"]["constraint_rank"] == 3
    assert tangent["tangent"]["exact_constraint_residual_zero"] is True
    assert design["version"] == "R0.11"
    assert design["design"]["square_constraint_determinant"] == "1458"
    assert design["design"]["coefficients"] == ["-4", "8", "-1", "-5", "1", "1"]
