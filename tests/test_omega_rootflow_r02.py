import json

import numpy as np
import pytest

from omega_rootflow_t import (
    audit_spectral_geometry,
    companion_crosscheck,
    companion_matrix,
    continue_roots_adaptive,
    inverse_design_roots,
    linearized_inverse_design,
    log_abs_discriminant,
    match_roots,
    propagate_root_covariance,
    roots,
)
from omega_rootflow_t.cli import main


def test_companion_matrix_eigenvalues_crosscheck_direct_roots() -> None:
    coeffs = np.array([1.0, -3.0, 0.0, 1.0])
    direct = roots(coeffs)
    eigenvalues = np.linalg.eigvals(companion_matrix(coeffs))
    assert np.allclose(direct, match_roots(direct, eigenvalues), atol=1e-12)
    report = companion_crosscheck(coeffs)
    assert report.relative_error < 1e-12


def test_log_discriminant_matches_quadratic_closed_form() -> None:
    coeffs = np.array([-1.0, 0.0, 1.0])
    assert np.isclose(np.exp(log_abs_discriminant(coeffs)), 4.0, atol=1e-12)


def test_spectral_audit_detects_root_collision() -> None:
    report = audit_spectral_geometry([1.0, -2.0, 1.0], collision_tolerance=1e-5)
    assert report.near_collision
    assert report.status == "OAK_WARN_ROOT_COLLISION"
    assert report.theorem_claimed is False
    assert report.scientific_validation_claimed is False


def test_root_covariance_is_hermitian_positive_semidefinite() -> None:
    coeffs = np.array([-1.0, 0.0, 1.0])
    covariance = np.diag([1e-4, 2e-4, 3e-4])
    propagated = propagate_root_covariance(coeffs, covariance)
    assert np.allclose(propagated, propagated.conj().T, atol=1e-14)
    assert np.min(np.linalg.eigvalsh(propagated)) > -1e-12
    assert np.all(np.real(np.diag(propagated)) > 0.0)


def test_linearized_inverse_design_solves_gauge_fixed_quadratic_update() -> None:
    coeffs = np.array([-1.0, 0.0, 1.0])
    rr = roots(coeffs)
    desired = np.array([-0.1, 0.2], dtype=np.complex128)
    result = linearized_inverse_design(coeffs, rr, desired)
    assert result.free_indices == (0, 1)
    assert result.real_coefficients
    assert result.residual_norm < 1e-12
    assert np.allclose(result.predicted_root_update, desired, atol=1e-12)
    assert result.coefficient_update[-1] == 0.0


def test_iterative_inverse_design_recovers_target_monic_quadratic() -> None:
    target = np.array([-1.1, 1.3], dtype=np.complex128)
    result = inverse_design_roots([-1.0, 0.0, 1.0], target)
    assert result.converged
    assert result.root_error_norm < 1e-10
    assert np.allclose(result.coefficients.real, [-1.43, -0.2, 1.0], atol=1e-9)
    assert np.allclose(result.roots, match_roots(result.roots, target), atol=1e-10)
    assert result.theorem_claimed is False


def test_adaptive_continuation_shrinks_steps_near_cubic_discriminant() -> None:
    start = np.array([0.0, -3.0, 0.0, 1.0])
    end = np.array([1.99, -3.0, 0.0, 1.0])
    result = continue_roots_adaptive(
        start,
        end,
        initial_step=0.25,
        minimum_step=1e-6,
        maximum_step=0.25,
        predictor_tolerance=1e-3,
        singularity_tolerance=1e-6,
    )
    expected = match_roots(result.final_roots, roots(end))
    assert result.status == "OAK_PASS_ADAPTIVE_CONTINUATION"
    assert np.allclose(result.final_roots, expected, atol=1e-10)
    assert result.minimum_step_size < 0.25
    assert max(step.corrected_residual for step in result.steps) < 1e-9


def test_adaptive_continuation_refuses_singular_start() -> None:
    with pytest.raises(np.linalg.LinAlgError):
        continue_roots_adaptive(
            [2.0, -3.0, 0.0, 1.0],
            [1.9, -3.0, 0.0, 1.0],
            singularity_tolerance=1e-5,
        )


def test_r02_cli_inverse_design_and_spectral_commands(tmp_path) -> None:
    inverse_output = tmp_path / "inverse.json"
    assert main(
        [
            "inverse-design",
            "--coeffs",
            "-1,0,1",
            "--target-roots=-1.1,1.3",
            "--output",
            str(inverse_output),
        ]
    ) == 0
    inverse = json.loads(inverse_output.read_text(encoding="utf-8"))
    assert inverse["version"] == "R0.6"
    assert inverse["converged"] is True
    assert inverse["claims"]["theorem_claimed"] is False

    spectral_output = tmp_path / "spectral.json"
    assert main(["spectral", "--coeffs", "-1,0,1", "--output", str(spectral_output)]) == 0
    spectral = json.loads(spectral_output.read_text(encoding="utf-8"))
    assert spectral["audit"]["status"] == "OAK_PASS_SPECTRAL_CROSSCHECK"
