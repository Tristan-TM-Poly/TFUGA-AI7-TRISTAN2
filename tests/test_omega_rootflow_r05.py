import json

import numpy as np

from omega_rootflow_t import (
    audit_discriminant,
    audit_invariants,
    discriminant_from_resultant,
    elementary_symmetric_from_coefficients,
    elementary_symmetric_from_roots,
    match_roots,
    newton_power_sums,
    parameter_root_kinematics,
    polynomial_resultant,
    power_sum_jacobian,
    power_sums_from_roots,
    residue_moments,
    roots,
    single_coefficient_collision_atlas,
    taylor_predict_roots,
    triangular_power_sum_sensitivity,
    vieta_jacobian,
)
from omega_rootflow_t.cli import main


def test_vieta_coordinates_match_known_root_factorization() -> None:
    # (z+2)(z-1)(z-3) = z^3 - 2z^2 - 5z + 6.
    coeffs = np.array([6.0, -5.0, -2.0, 1.0])
    rr = roots(coeffs)
    from_coeffs = elementary_symmetric_from_coefficients(coeffs)
    from_roots = elementary_symmetric_from_roots(rr)
    assert np.allclose(from_coeffs, [1.0, 2.0, -5.0, -6.0], atol=1e-12)
    assert np.allclose(from_coeffs, from_roots, atol=1e-12)


def test_vieta_jacobian_has_exact_projective_null_direction() -> None:
    coeffs = np.array([6.0, -5.0, -2.0, 1.0])
    jac = vieta_jacobian(coeffs)
    assert jac.shape == (3, 4)
    assert np.max(np.abs(jac @ coeffs)) < 1e-12
    # e1 = -a2/a3, so d e1 / d a2 = -1/a3.
    assert np.isclose(jac[0, 2], -1.0)


def test_newton_recurrence_matches_direct_root_power_sums_beyond_degree() -> None:
    coeffs = np.array([6.0, -5.0, -2.0, 1.0])
    rr = roots(coeffs)
    direct = power_sums_from_roots(rr, 9)
    recurrent = newton_power_sums(coeffs, 9)
    assert np.allclose(recurrent, direct, atol=2e-10, rtol=2e-12)
    assert np.allclose(recurrent[:4], [3.0, 2.0, 14.0, 20.0], atol=1e-12)


def test_residue_moment_identity_and_triangular_sensitivity_are_exact() -> None:
    coeffs = np.array([6.0, -5.0, -2.0, 1.0])
    residues = residue_moments(coeffs, 2)
    assert np.allclose(residues[:2], 0.0, atol=1e-12)
    assert np.isclose(residues[2], 1.0, atol=1e-12)

    observed = power_sum_jacobian(coeffs, 3)[:, :3]
    expected = triangular_power_sum_sensitivity(coeffs)
    mask = np.isfinite(expected.real)
    assert np.allclose(observed[mask], expected[mask], atol=2e-12)


def test_constant_coefficient_first_changes_cubic_power_sum_at_order_three() -> None:
    coeffs = np.array([0.7, -1.3, 0.2, 1.0])
    jac = power_sum_jacobian(coeffs, 3)
    assert abs(jac[0, 0]) < 1e-11
    assert abs(jac[1, 0]) < 1e-11
    assert np.isclose(jac[2, 0], -3.0, atol=1e-10)

    epsilon = 1e-7
    plus = coeffs.copy()
    minus = coeffs.copy()
    plus[0] += epsilon
    minus[0] -= epsilon
    p_plus = power_sums_from_roots(roots(plus), 3)
    p_minus = power_sums_from_roots(roots(minus), 3)
    finite_difference = (p_plus - p_minus) / (2.0 * epsilon)
    assert abs(finite_difference[1]) < 1e-7
    assert abs(finite_difference[2]) < 1e-7
    assert np.isclose(finite_difference[3], -3.0, rtol=2e-6, atol=2e-6)


def test_full_invariant_audit_passes_well_separated_cubic() -> None:
    report = audit_invariants([6.0, -5.0, -2.0, 1.0])
    assert report.passed
    assert report.max_vieta_error < 1e-11
    assert report.max_newton_error < 1e-9
    assert report.max_residue_identity_error < 1e-11
    assert report.projective_vieta_null_error < 1e-12
    assert report.theorem_claimed is False


def test_resultant_discriminant_matches_quadratic_closed_form() -> None:
    # 4 z^2 + 3 z + 2 -> b^2 - 4ac = 9 - 32 = -23.
    coeffs = np.array([2.0, 3.0, 4.0])
    discriminant = discriminant_from_resultant(coeffs)
    assert np.isclose(discriminant, -23.0, atol=1e-12)
    derivative = np.array([3.0, 8.0])
    resultant = polynomial_resultant(coeffs, derivative)
    assert np.isclose(-resultant / coeffs[-1], -23.0, atol=1e-12)
    report = audit_discriminant(coeffs)
    assert report.passed
    assert report.relative_error < 1e-12


def test_discriminant_audit_identifies_exact_double_root() -> None:
    report = audit_discriminant([1.0, -2.0, 1.0])
    assert report.near_collision
    assert report.status == "OAK_PASS_DISCRIMINANT_COLLISION"
    assert abs(report.resultant_discriminant) < 1e-12


def test_constant_shift_collision_atlas_for_z5_minus_5z_is_regular_four_gon() -> None:
    coeffs = np.array([0.0, -5.0, 0.0, 0.0, 0.0, 1.0])
    atlas = single_coefficient_collision_atlas(coeffs, 0)
    assert atlas.status == "OAK_PASS_SINGLE_COEFFICIENT_COLLISIONS"
    assert len(atlas.candidates) == 4
    parameters = np.asarray([item.parameter for item in atlas.candidates])
    assert np.allclose(np.abs(parameters), 4.0, atol=1e-10)
    assert np.allclose(parameters**4, 4.0**4, atol=1e-8)
    assert atlas.maximum_residual < 1e-9


def test_leading_coefficient_shift_reports_projective_infinity_transition() -> None:
    atlas = single_coefficient_collision_atlas([-1.0, 0.0, 1.0], 2)
    assert atlas.candidates == ()
    assert atlas.infinity_transition_parameter == -1.0 + 0j
    assert atlas.status == "OAK_PASS_SINGLE_COEFFICIENT_COLLISIONS"


def test_second_order_root_kinematics_improves_sqrt_parameter_prediction() -> None:
    # P(z,t)=z^2-t at t=1: r=sqrt(t), r'=1/(2r), r''=-1/(4r^3).
    coeffs = np.array([-1.0, 0.0, 1.0])
    coefficient_velocity = np.array([-1.0, 0.0, 0.0])
    state = parameter_root_kinematics(coeffs, coefficient_velocity)
    positive_index = int(np.argmin(np.abs(state.roots - 1.0)))
    assert np.isclose(state.velocities[positive_index], 0.5, atol=1e-12)
    assert np.isclose(state.accelerations[positive_index], -0.25, atol=1e-12)

    delta = 0.1
    first = taylor_predict_roots(state, delta, order=1)
    second = taylor_predict_roots(state, delta, order=2)
    exact = match_roots(state.roots, roots([-1.1, 0.0, 1.0]))
    first_error = np.linalg.norm(first - exact)
    second_error = np.linalg.norm(second - exact)
    assert second_error < first_error
    assert state.status == "OAK_PASS_PARAMETER_KINEMATICS"
    assert state.theorem_claimed is False


def test_r05_cli_invariants_discriminant_collisions_and_kinematics(tmp_path) -> None:
    paths = {
        "invariants": tmp_path / "invariants.json",
        "discriminant": tmp_path / "discriminant.json",
        "collisions": tmp_path / "collisions.json",
        "kinematics": tmp_path / "kinematics.json",
    }
    assert main(["invariants", "--coeffs", "6,-5,-2,1", "--output", str(paths["invariants"])]) == 0
    assert main(["discriminant", "--coeffs", "2,3,4", "--output", str(paths["discriminant"])]) == 0
    assert main(
        [
            "collisions",
            "--coeffs",
            "0,-5,0,0,0,1",
            "--coefficient-degree",
            "0",
            "--output",
            str(paths["collisions"]),
        ]
    ) == 0
    assert main(
        [
            "kinematics",
            "--coeffs=-1,0,1",
            "--velocity=-1,0,0",
            "--delta",
            "0.1",
            "--output",
            str(paths["kinematics"]),
        ]
    ) == 0

    invariants = json.loads(paths["invariants"].read_text(encoding="utf-8"))
    discriminant = json.loads(paths["discriminant"].read_text(encoding="utf-8"))
    collisions = json.loads(paths["collisions"].read_text(encoding="utf-8"))
    kinematics = json.loads(paths["kinematics"].read_text(encoding="utf-8"))
    assert invariants["version"] == "R0.5"
    assert invariants["audit"]["status"] == "OAK_PASS_VIETA_NEWTON_RESIDUE"
    assert discriminant["audit"]["status"] == "OAK_PASS_DISCRIMINANT_CROSSCHECK"
    assert len(collisions["atlas"]["candidates"]) == 4
    assert len(kinematics["second_order_prediction"]) == 2
