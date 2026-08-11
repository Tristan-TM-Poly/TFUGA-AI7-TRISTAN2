import json

import numpy as np

from omega_rootflow_t import (
    audit_multiplicity_prediction,
    exact_root_multiplicity,
    falling_factorial,
    multiplicity_tangent_space,
)
from omega_rootflow_t.cli import main


def test_falling_factorial_matches_derivative_coefficients() -> None:
    assert falling_factorial(5, 0) == 1
    assert falling_factorial(5, 1) == 5
    assert falling_factorial(5, 2) == 20
    assert falling_factorial(5, 5) == 120
    assert falling_factorial(3, 4) == 0


def test_exact_rational_root_multiplicity_is_detected_by_repeated_division() -> None:
    assert exact_root_multiplicity([-1, 3, -3, 1], 1) == 3
    assert exact_root_multiplicity([1, -4, 6, -4, 1], "1") == 4
    assert exact_root_multiplicity([1, -4, 6, -4, 1], 2) == 0


def test_triple_root_tangent_space_has_expected_rank_and_dimension() -> None:
    # (z-1)^3 = z^3 - 3z^2 + 3z - 1.
    tangent = multiplicity_tangent_space(
        [-1.0, 3.0, -3.0, 1.0],
        1.0,
        3,
        [0, 1, 2, 3],
    )
    assert tangent.status == "OAK_PASS_MULTIPLICITY_TANGENT_SPACE"
    assert tangent.constraint_matrix.shape == (2, 4)
    assert tangent.constraint_rank == 2
    assert tangent.tangent_dimension == 2
    assert tangent.tangent_basis.shape == (2, 4)
    assert tangent.tangent_constraint_residual < 1e-12
    assert np.isclose(tangent.first_nonzero_derivative_magnitude, 6.0)
    assert tangent.theorem_claimed is False


def test_triple_root_tangent_constraints_match_closed_form_rows() -> None:
    tangent = multiplicity_tangent_space(
        [-1.0, 3.0, -3.0, 1.0],
        1.0,
        3,
        [0, 1, 2, 3],
    )
    expected = np.array(
        [
            [1.0, 1.0, 1.0, 1.0],
            [0.0, 1.0, 2.0, 3.0],
        ]
    )
    assert np.allclose(tangent.constraint_matrix, expected, atol=1e-12)
    assert np.allclose(tangent.constraint_matrix @ tangent.tangent_basis.T, 0.0, atol=1e-12)


def test_triple_root_prediction_has_quadratic_residual_scaling() -> None:
    coeffs = np.array([-1.0, 3.0, -3.0, 1.0])
    tangent = multiplicity_tangent_space(coeffs, 1.0, 3, [0, 1, 2, 3])
    coarse = audit_multiplicity_prediction(coeffs, tangent, epsilon=1e-3)
    fine = audit_multiplicity_prediction(coeffs, tangent, epsilon=5e-4)
    assert coarse.status == "OAK_PASS_MULTIPLICITY_TANGENT_PREDICTION"
    assert fine.status == "OAK_PASS_MULTIPLICITY_TANGENT_PREDICTION"
    assert fine.maximum_constraint_residual < 0.35 * coarse.maximum_constraint_residual
    for coarse_residual, fine_residual in zip(
        coarse.residuals_by_derivative_order,
        fine.residuals_by_derivative_order,
        strict=True,
    ):
        if coarse_residual > 1e-15:
            assert fine_residual < 0.35 * coarse_residual


def test_requested_triple_model_refuses_quadruple_root() -> None:
    tangent = multiplicity_tangent_space(
        [1.0, -4.0, 6.0, -4.0, 1.0],
        1.0,
        3,
        [0, 1, 2, 3, 4],
    )
    assert tangent.status == "OAK_REFUSE_MULTIPLICITY_HIGHER_THAN_REQUESTED"
    assert tangent.tangent_dimension == 0


def test_quadruple_root_tangent_space_generalizes_without_special_case() -> None:
    tangent = multiplicity_tangent_space(
        [1.0, -4.0, 6.0, -4.0, 1.0],
        1.0,
        4,
        [0, 1, 2, 3, 4],
    )
    assert tangent.status == "OAK_PASS_MULTIPLICITY_TANGENT_SPACE"
    assert tangent.constraint_matrix.shape == (3, 5)
    assert tangent.constraint_rank == 3
    assert tangent.tangent_dimension == 2
    assert np.isclose(tangent.first_nonzero_derivative_magnitude, 24.0)


def test_r07_cli_exact_multiplicity_and_tangent_surfaces(tmp_path) -> None:
    multiplicity_output = tmp_path / "multiplicity.json"
    tangent_output = tmp_path / "stratum.json"
    assert main(
        [
            "exact-multiplicity",
            "--coeffs=-1,3,-3,1",
            "--root",
            "1",
            "--output",
            str(multiplicity_output),
        ]
    ) == 0
    assert main(
        [
            "multiplicity-tangent",
            "--coeffs=-1,3,-3,1",
            "--critical-root",
            "1",
            "--multiplicity",
            "3",
            "--degrees",
            "0,1,2,3",
            "--epsilon",
            "0.001",
            "--output",
            str(tangent_output),
        ]
    ) == 0
    multiplicity = json.loads(multiplicity_output.read_text(encoding="utf-8"))
    tangent = json.loads(tangent_output.read_text(encoding="utf-8"))
    assert multiplicity["version"] == "R0.7"
    assert multiplicity["multiplicity"] == 3
    assert tangent["stratum"]["multiplicity"] == 3
    assert tangent["stratum"]["tangent_dimension"] == 2
    assert tangent["prediction_audit"]["status"] == "OAK_PASS_MULTIPLICITY_TANGENT_PREDICTION"
