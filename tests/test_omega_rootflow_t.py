import numpy as np
import pytest

from omega_rootflow_t import (
    audit_rootflow,
    basis_root_differential,
    continue_roots,
    degree_perturbation_sensitivity,
    finite_difference_root_jacobian,
    match_roots,
    projective_scaling_residual,
    root_conditions,
    root_hessian,
    root_jacobian,
    root_velocity,
    roots,
)
from omega_rootflow_t.cli import analyze_payload, main


def test_quadratic_coefficient_jacobian_matches_closed_form() -> None:
    coeffs = np.array([-1.0, 0.0, 1.0])
    rr = roots(coeffs)
    jac = root_jacobian(coeffs, rr)
    assert np.allclose(jac[:, 0], -1.0 / (2.0 * rr), atol=1e-12)
    assert np.allclose(jac[:, 1], -0.5, atol=1e-12)


def test_analytic_jacobian_matches_independent_finite_difference() -> None:
    coeffs = np.array([0.7, -1.3, 0.2, 1.0])
    rr = roots(coeffs)
    analytic = root_jacobian(coeffs, rr)
    numeric = finite_difference_root_jacobian(coeffs, step=2e-7)
    assert np.allclose(analytic, numeric, atol=2e-7, rtol=2e-6)


def test_projective_scaling_direction_is_null() -> None:
    coeffs = np.array([2.0, -3.0, 0.25, 1.0])
    residual = projective_scaling_residual(coeffs)
    assert np.max(np.abs(residual)) < 1e-11
    velocity = root_velocity(coeffs, coeffs)
    assert np.max(np.abs(velocity)) < 1e-11


def test_generic_basis_differential_matches_monomial_jacobian_row() -> None:
    coeffs = np.array([1.0, -2.0, 0.0, 1.0])
    root = complex(roots(coeffs)[0])
    delta = np.array([0.1, -0.2, 0.05, 0.01])
    jac = root_jacobian(coeffs, [root])[0]
    p1 = sum(k * coeffs[k] * root ** (k - 1) for k in range(1, coeffs.size))
    basis = np.array([root**k for k in range(coeffs.size)])
    generic = basis_root_differential(
        derivative_at_root=p1,
        basis_values_at_root=basis,
        coefficient_differential=delta,
    )
    assert np.allclose(generic, jac @ delta)


def test_root_hessian_is_symmetric_and_predicts_second_coefficient_derivative() -> None:
    coeffs = np.array([-1.0, 0.0, 1.0])
    rr = roots(coeffs)
    hessian = root_hessian(coeffs, rr)
    assert np.allclose(hessian, np.swapaxes(hessian, 1, 2), atol=1e-12)
    idx = int(np.argmin(np.abs(rr - 1.0)))
    assert np.isclose(hessian[idx, 0, 0].real, -0.25, atol=1e-12)


def test_degree_perturbation_formula_against_small_added_term() -> None:
    coeffs = np.array([-1.0, 0.0, 1.0])
    root = 1.0 + 0j
    sensitivity = degree_perturbation_sensitivity(coeffs, root, 3)
    epsilon = 1e-7
    augmented = np.array([-1.0, 0.0, 1.0, epsilon])
    perturbed = match_roots(
        np.array([1.0 + 0j, -1.0 + 0j, -1.0 / epsilon + 0j]), roots(augmented)
    )[0]
    observed = (perturbed - root) / epsilon
    assert np.isclose(observed, sensitivity, rtol=2e-5, atol=2e-5)


def test_predictor_corrector_continuation_tracks_cubic_away_from_discriminant() -> None:
    start = np.array([0.0, -3.0, 0.0, 1.0])
    end = np.array([1.0, -3.0, 0.0, 1.0])
    result = continue_roots(start, end, steps=20)
    expected = match_roots(result.final_roots, roots(end))
    assert np.allclose(result.final_roots, expected, atol=1e-10)
    assert max(step.corrected_residual for step in result.steps) < 1e-10
    assert result.steps[-1].minimum_derivative > 0.1


def test_near_multiple_root_is_flagged_and_singular_jacobian_is_refused() -> None:
    coeffs = np.array([1.0, -2.0, 1.0])
    conditions = root_conditions(coeffs, singularity_tolerance=1e-6)
    assert any(item.near_singular for item in conditions)
    with pytest.raises(np.linalg.LinAlgError):
        root_jacobian(coeffs, [1.0 + 0j], singularity_tolerance=1e-8)


def test_oak_audit_and_cli_are_claim_safe(tmp_path) -> None:
    coeffs = np.array([0.5, -1.0, 0.2, 1.0])
    audit = audit_rootflow(coeffs)
    assert audit.passed
    assert audit.theorem_claimed is False
    assert audit.scientific_validation_claimed is False
    payload = analyze_payload(coeffs.astype(complex))
    assert payload["system"] == "Ω-ROOTFLOW-T∞"
    assert payload["claims"]["theorem_claimed"] is False
    output = tmp_path / "rootflow.json"
    assert main(["analyze", "--coeffs", "0.5,-1,0.2,1", "--output", str(output)]) == 0
    assert "Ω-ROOTFLOW-T∞" in output.read_text(encoding="utf-8")
