import json

import numpy as np

from omega_rootflow_t import (
    RootCluster,
    audit_multi_cluster_prediction,
    fixed_cluster_hermite_matrix,
    hermite_inverse_design,
    mobile_cluster_constraint_matrix,
    multi_cluster_tangent_space,
)
from omega_rootflow_t.cli import main


COEFFS = np.array([-4.0, 8.0, -1.0, -5.0, 1.0, 1.0])  # (z-1)^3 (z+2)^2
CLUSTERS = (RootCluster(1.0, 3), RootCluster(-2.0, 2))


def test_stacked_mobile_cluster_matrix_has_expected_confluent_rows() -> None:
    matrix = mobile_cluster_constraint_matrix(CLUSTERS, tuple(range(6)))
    expected = np.array(
        [
            [1, 1, 1, 1, 1, 1],
            [0, 1, 2, 3, 4, 5],
            [1, -2, 4, -8, 16, -32],
        ],
        dtype=np.complex128,
    )
    assert matrix.shape == (3, 6)
    assert np.allclose(matrix, expected, atol=1e-12)


def test_multicluster_tangent_rank_matches_partition_codimension() -> None:
    tangent = multi_cluster_tangent_space(COEFFS, CLUSTERS, tuple(range(6)))
    assert tangent.status == "OAK_PASS_MULTICLUSTER_TANGENT_SPACE"
    assert tangent.constraint_rank == 3
    assert tangent.expected_full_space_codimension == 3
    assert tangent.tangent_dimension == 3
    assert tangent.cluster_velocities.shape == (3, 2)
    assert tangent.tangent_constraint_residual < 1e-12
    assert tangent.maximum_cluster_constraint_residual < 1e-12
    assert tangent.theorem_claimed is False


def test_multicluster_first_order_prediction_is_quadratically_accurate() -> None:
    tangent = multi_cluster_tangent_space(COEFFS, CLUSTERS, tuple(range(6)))
    coarse = audit_multi_cluster_prediction(COEFFS, tangent, epsilon=1e-3)
    fine = audit_multi_cluster_prediction(COEFFS, tangent, epsilon=5e-4)
    assert coarse.status == "OAK_PASS_MULTICLUSTER_TANGENT_PREDICTION"
    assert fine.status == "OAK_PASS_MULTICLUSTER_TANGENT_PREDICTION"
    assert fine.maximum_constraint_residual < 0.4 * coarse.maximum_constraint_residual


def test_fixed_hermite_matrix_has_five_constraints_for_partition_3_2() -> None:
    matrix = fixed_cluster_hermite_matrix(CLUSTERS, tuple(range(6)))
    assert matrix.shape == (5, 6)
    assert np.linalg.matrix_rank(matrix) == 5


def test_monic_real_hermite_inverse_design_recovers_known_polynomial() -> None:
    start = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    result = hermite_inverse_design(
        start,
        CLUSTERS,
        free_degrees=(0, 1, 2, 3, 4),
        real_coefficients=True,
    )
    assert result.status == "OAK_PASS_HERMITE_INVERSE_DESIGN"
    assert result.constraint_rank == 5
    assert result.residual_after < 1e-10
    assert np.allclose(result.coefficients, COEFFS, atol=1e-10)
    assert result.coefficients[-1] == 1.0


def test_real_inverse_design_handles_conjugate_double_clusters() -> None:
    start = np.array([0.0, 0.0, 0.0, 0.0, 1.0])
    clusters = (RootCluster(1j, 2), RootCluster(-1j, 2))
    result = hermite_inverse_design(
        start,
        clusters,
        free_degrees=(0, 1, 2, 3),
        real_coefficients=True,
    )
    assert result.status == "OAK_PASS_HERMITE_INVERSE_DESIGN"
    assert result.residual_after < 1e-10
    assert np.allclose(result.coefficients, [1.0, 0.0, 2.0, 0.0, 1.0], atol=1e-10)


def test_complex_inverse_design_can_use_complex_cluster_locations() -> None:
    start = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.complex128)
    clusters = (RootCluster(1 + 1j, 2), RootCluster(-2j, 1))
    result = hermite_inverse_design(
        start,
        clusters,
        free_degrees=(0, 1, 2),
        real_coefficients=False,
    )
    assert result.status == "OAK_PASS_HERMITE_INVERSE_DESIGN"
    assert result.constraint_rank == 3
    assert result.residual_after < 1e-9


def test_multicluster_refuses_incorrect_requested_partition() -> None:
    wrong = (RootCluster(1.0, 2), RootCluster(-2.0, 2))
    tangent = multi_cluster_tangent_space(COEFFS, wrong, tuple(range(6)))
    assert tangent.status == "OAK_REFUSE_CLUSTER_MULTIPLICITY_HIGHER_THAN_REQUESTED"
    assert tangent.tangent_dimension == 0


def test_r10_cli_multicluster_tangent_and_hermite_design(tmp_path) -> None:
    tangent_path = tmp_path / "tangent.json"
    design_path = tmp_path / "design.json"
    assert main([
        "multi-cluster-tangent",
        "--coeffs=-4,8,-1,-5,1,1",
        "--clusters", "1:3,-2:2",
        "--degrees", "0,1,2,3,4,5",
        "--epsilon", "0.001",
        "--output", str(tangent_path),
    ]) == 0
    assert main([
        "hermite-design",
        "--coeffs=0,0,0,0,0,1",
        "--clusters", "1:3,-2:2",
        "--free-degrees", "0,1,2,3,4",
        "--real-coefficients",
        "--output", str(design_path),
    ]) == 0
    tangent = json.loads(tangent_path.read_text(encoding="utf-8"))
    design = json.loads(design_path.read_text(encoding="utf-8"))
    assert tangent["version"] == "R0.10"
    assert tangent["tangent"]["constraint_rank"] == 3
    assert tangent["prediction_audit"]["status"] == "OAK_PASS_MULTICLUSTER_TANGENT_PREDICTION"
    assert design["version"] == "R0.10"
    assert design["design"]["status"] == "OAK_PASS_HERMITE_INVERSE_DESIGN"
    recovered = [item[0] for item in design["design"]["coefficients"]]
    assert np.allclose(recovered, [-4, 8, -1, -5, 1, 1], atol=1e-10)
