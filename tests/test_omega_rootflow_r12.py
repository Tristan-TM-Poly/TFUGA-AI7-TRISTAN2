import json

import numpy as np

from omega_rootflow_t import (
    RootCluster,
    analyze_joint_direction,
    design_joint_unfolding,
    joint_unfolding_map,
    multi_cluster_tangent_space,
)
from omega_rootflow_t.cli import main


COEFFS = np.array([-4.0, 8.0, -1.0, -5.0, 1.0, 1.0])
CLUSTERS = (RootCluster(1.0, 3), RootCluster(-2.0, 2))
DEGREES = tuple(range(6))


def test_joint_unfolding_map_has_same_rank_as_mobile_stratum() -> None:
    joint = joint_unfolding_map(COEFFS, CLUSTERS, DEGREES)
    assert joint.status == "OAK_PASS_JOINT_UNFOLDING_MAP"
    assert joint.jet_matrix.shape == (3, 6)
    assert joint.jet_rank == 3
    assert joint.mobile_constraint_rank == 3
    assert joint.kernel_rank_agreement
    assert joint.tangent_dimension == 3
    assert joint.row_scaling_residual < 1e-12
    assert joint.theorem_claimed is False


def test_mobile_tangent_basis_produces_zero_joint_split_jet() -> None:
    joint = joint_unfolding_map(COEFFS, CLUSTERS, DEGREES)
    tangent = multi_cluster_tangent_space(COEFFS, CLUSTERS, DEGREES)
    for direction in tangent.tangent_basis:
        analysis = analyze_joint_direction(joint, direction)
        assert np.linalg.norm(analysis.joint_jet) < 1e-10
        assert analysis.first_order_stratum_tangent
        assert analysis.active_cluster_count == 0
        assert analysis.status == "OAK_PASS_JOINT_TANGENT_DIRECTION"


def test_selectively_split_triple_cluster_with_constant_jet() -> None:
    joint = joint_unfolding_map(COEFFS, CLUSTERS, DEGREES)
    design = design_joint_unfolding(joint, [1.0, 0.0, 0.0], real_coefficients=True)
    assert design.status == "OAK_PASS_JOINT_UNFOLDING_DESIGN"
    assert design.residual_norm < 1e-10
    assert np.max(np.abs(design.direction.imag)) < 1e-12
    first, second = design.analysis.signatures
    assert first.first_active_order == 0
    assert np.isclose(first.predicted_puiseux_exponent, 1.0 / 3.0)
    assert first.splitting_branch_count == 3
    assert second.first_active_order is None
    assert second.status == "OAK_PASS_CLUSTER_FIRST_ORDER_PRESERVED"


def test_selectively_split_triple_cluster_with_linear_jet() -> None:
    joint = joint_unfolding_map(COEFFS, CLUSTERS, DEGREES)
    design = design_joint_unfolding(joint, [0.0, 1.0, 0.0], real_coefficients=True)
    assert design.residual_norm < 1e-10
    first, second = design.analysis.signatures
    assert first.first_active_order == 1
    assert first.local_factor_order == 1
    assert first.splitting_branch_count == 2
    assert np.isclose(first.predicted_puiseux_exponent, 0.5)
    assert second.first_active_order is None


def test_selectively_split_double_cluster_while_preserving_triple() -> None:
    joint = joint_unfolding_map(COEFFS, CLUSTERS, DEGREES)
    design = design_joint_unfolding(joint, [0.0, 0.0, 1.0], real_coefficients=True)
    assert design.residual_norm < 1e-10
    first, second = design.analysis.signatures
    assert first.first_active_order is None
    assert second.first_active_order == 0
    assert second.splitting_branch_count == 2
    assert np.isclose(second.predicted_puiseux_exponent, 0.5)


def test_joint_target_design_reports_unreachable_restricted_family() -> None:
    joint = joint_unfolding_map(COEFFS, CLUSTERS, (0,))
    design = design_joint_unfolding(joint, [0.0, 1.0, 0.0], real_coefficients=True)
    assert design.status == "OAK_WARN_JOINT_UNFOLDING_TARGET_RESIDUAL"
    assert design.residual_norm > 0.1


def test_joint_map_block_boundaries_match_cluster_unfolding_dimensions() -> None:
    joint = joint_unfolding_map(COEFFS, CLUSTERS, DEGREES)
    assert [(block.row_start, block.row_stop) for block in joint.blocks] == [(0, 2), (2, 3)]
    assert np.isclose(joint.blocks[0].leading_local_coefficient, 9.0)
    assert np.isclose(joint.blocks[1].leading_local_coefficient, -27.0)


def test_r12_cli_joint_unfolding_and_selective_design(tmp_path) -> None:
    map_path = tmp_path / "joint.json"
    design_path = tmp_path / "design.json"
    assert main([
        "joint-unfolding",
        "--coeffs=-4,8,-1,-5,1,1",
        "--clusters", "1:3,-2:2",
        "--degrees", "0,1,2,3,4,5",
        "--direction", "1,0,0,0,0,0",
        "--output", str(map_path),
    ]) == 0
    assert main([
        "joint-unfolding-design",
        "--coeffs=-4,8,-1,-5,1,1",
        "--clusters", "1:3,-2:2",
        "--degrees", "0,1,2,3,4,5",
        "--target-jet", "1,0,0",
        "--real-coefficients",
        "--output", str(design_path),
    ]) == 0
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    design = json.loads(design_path.read_text(encoding="utf-8"))
    assert mapping["version"] == "R0.12"
    assert mapping["unfolding"]["kernel_rank_agreement"] is True
    assert design["version"] == "R0.12"
    assert design["design"]["status"] == "OAK_PASS_JOINT_UNFOLDING_DESIGN"
    signatures = design["design"]["analysis"]["signatures"]
    assert np.isclose(signatures[0]["predicted_puiseux_exponent"], 1.0 / 3.0)
    assert signatures[1]["first_active_order"] is None
