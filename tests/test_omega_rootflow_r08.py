import json

import numpy as np

from omega_rootflow_t import (
    analyze_unfolding_direction,
    complex_parameter_realification,
    local_unfolding_map,
    local_unfolding_roots,
    match_roots,
    multiplicity_tangent_space,
    real_parameter_constraint_matrix,
    real_parameter_tangent_space,
    roots,
)
from omega_rootflow_t.cli import main


def test_real_root_real_parameter_codimension_matches_complex_rank() -> None:
    # (z-1)^2(z+2) = z^3 - 3z + 2.
    coeffs = np.array([2.0, -3.0, 0.0, 1.0])
    real = real_parameter_tangent_space(coeffs, 1.0, 2, (0, 1, 2, 3))
    assert real.complex_constraint_rank == 1
    assert real.complex_tangent_dimension == 3
    assert real.real_constraint_rank == 1
    assert real.real_codimension == 1
    assert real.real_tangent_dimension == 3
    assert real.tangent_constraint_residual < 1e-12
    assert real.status == "OAK_PASS_REAL_PARAMETER_TANGENT_SPACE"


def test_nonreal_double_root_doubles_real_coefficient_codimension() -> None:
    # (z^2+1)^2 has a double root at i and real coefficients.
    coeffs = np.array([1.0, 0.0, 2.0, 0.0, 1.0])
    complex_space = multiplicity_tangent_space(coeffs, 1j, 2, (0, 1, 2, 3, 4))
    real = real_parameter_tangent_space(coeffs, 1j, 2, (0, 1, 2, 3, 4))
    assert complex_space.constraint_rank == 1
    assert complex_space.tangent_dimension == 4
    assert real.real_constraint_rank == 2
    assert real.real_codimension == 2
    assert real.real_tangent_dimension == 3
    expected = np.array([[1, 0, -1, 0, 1], [0, 1, 0, -1, 0]], dtype=float)
    assert np.allclose(real.real_constraint_matrix, expected, atol=1e-12)


def test_realification_matrices_encode_complex_constraint() -> None:
    matrix = np.array([[1 + 2j, 3 - 4j]], dtype=np.complex128)
    real_parameters = real_parameter_constraint_matrix(matrix)
    complex_parameters = complex_parameter_realification(matrix)
    assert real_parameters.shape == (2, 2)
    assert complex_parameters.shape == (2, 4)
    vector = np.array([2 - 1j, -0.5 + 3j])
    lhs = matrix @ vector
    packed = np.concatenate((vector.real, vector.imag))
    encoded = complex_parameters @ packed
    assert np.allclose(encoded, [lhs.real[0], lhs.imag[0]], atol=1e-12)


def test_z3_has_complete_two_dimensional_local_unfolding() -> None:
    unfolding = local_unfolding_map([0.0, 0.0, 0.0, 1.0], 0.0, 3, (0, 1, 2, 3))
    assert unfolding.unfolding_dimension == 2
    assert unfolding.jet_rank == 2
    assert unfolding.complete_first_order_unfolding
    assert unfolding.tangent_dimension == 2
    assert np.allclose(
        unfolding.jet_matrix,
        np.array([[1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.complex128),
        atol=1e-12,
    )
    assert unfolding.status == "OAK_PASS_COMPLETE_LOCAL_UNFOLDING"


def test_incomplete_parameter_family_is_reported_without_overclaim() -> None:
    unfolding = local_unfolding_map([0.0, 0.0, 0.0, 1.0], 0.0, 3, (0, 2, 3))
    assert unfolding.jet_rank == 1
    assert unfolding.unfolding_dimension == 2
    assert not unfolding.complete_first_order_unfolding
    assert unfolding.status == "OAK_PASS_PARTIAL_LOCAL_UNFOLDING"


def test_unfolding_direction_recovers_canonical_puiseux_exponents() -> None:
    cubic = local_unfolding_map([0.0, 0.0, 0.0, 1.0], 0.0, 3, (0, 1, 2, 3))
    constant = analyze_unfolding_direction(cubic, [1, 0, 0, 0])
    linear = analyze_unfolding_direction(cubic, [0, 1, 0, 0])
    tangent = analyze_unfolding_direction(cubic, [0, 0, 1, 0])
    assert constant.first_active_jet_order == 0
    assert np.isclose(constant.predicted_puiseux_exponent, 1.0 / 3.0)
    assert constant.splitting_branch_count == 3
    assert linear.first_active_jet_order == 1
    assert np.isclose(linear.predicted_puiseux_exponent, 0.5)
    assert linear.local_factor_order == 1
    assert linear.splitting_branch_count == 2
    assert tangent.first_active_jet_order is None
    assert tangent.predicted_puiseux_exponent is None
    assert tangent.status == "OAK_PASS_FIRST_ORDER_STRATUM_TANGENT_DIRECTION"


def test_transverse_plus_tangent_projection_reconstructs_direction() -> None:
    unfolding = local_unfolding_map([0.0, 0.0, 0.0, 1.0], 0.0, 3, (0, 1, 2, 3))
    direction = np.array([1.0, -2.0, 3.0, 4.0], dtype=np.complex128)
    analysis = analyze_unfolding_direction(unfolding, direction)
    assert np.allclose(
        analysis.tangent_component + analysis.transverse_component,
        direction,
        atol=1e-12,
    )
    assert np.linalg.norm(unfolding.jet_matrix @ analysis.tangent_component) < 1e-11


def test_local_unfolding_roots_are_exact_for_z3_plus_epsilon() -> None:
    unfolding = local_unfolding_map([0.0, 0.0, 0.0, 1.0], 0.0, 3, (0, 1, 2, 3))
    epsilon = 1e-4
    predicted = local_unfolding_roots(unfolding, [1, 0, 0, 0], epsilon)
    exact = roots([epsilon, 0.0, 0.0, 1.0])
    assert np.allclose(predicted, match_roots(predicted, exact), atol=1e-12)


def test_z4_plus_epsilon_z2_signature_is_square_root_with_two_persistent_factors() -> None:
    unfolding = local_unfolding_map([0.0, 0.0, 0.0, 0.0, 1.0], 0.0, 4, (0, 1, 2, 3, 4))
    direction = analyze_unfolding_direction(unfolding, [0, 0, 1, 0, 0])
    assert direction.first_active_jet_order == 2
    assert direction.local_factor_order == 2
    assert direction.splitting_branch_count == 2
    assert np.isclose(direction.predicted_puiseux_exponent, 0.5)


def test_r08_cli_realify_and_unfolding_surfaces(tmp_path) -> None:
    real_path = tmp_path / "real.json"
    unfold_path = tmp_path / "unfold.json"
    assert main([
        "real-tangent",
        "--coeffs", "1,0,2,0,1",
        "--critical-root", "1j",
        "--multiplicity", "2",
        "--degrees", "0,1,2,3,4",
        "--output", str(real_path),
    ]) == 0
    assert main([
        "unfolding",
        "--coeffs", "0,0,0,1",
        "--critical-root", "0",
        "--multiplicity", "3",
        "--degrees", "0,1,2,3",
        "--direction", "1,0,0,0",
        "--epsilon", "0.0001",
        "--output", str(unfold_path),
    ]) == 0
    real = json.loads(real_path.read_text(encoding="utf-8"))
    unfold = json.loads(unfold_path.read_text(encoding="utf-8"))
    assert real["version"] == "R0.8"
    assert real["real_tangent"]["real_codimension"] == 2
    assert unfold["version"] == "R0.8"
    assert unfold["unfolding"]["complete_first_order_unfolding"] is True
    assert np.isclose(unfold["direction_analysis"]["predicted_puiseux_exponent"], 1.0 / 3.0)
    assert len(unfold["local_model_roots"]) == 3
